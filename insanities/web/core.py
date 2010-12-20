# -*- coding: utf-8 -*-

__all__ = ['WebHandler', 'cases', 'HttpException', 'handler', 'Reverse']

import logging
import types
import httplib
from inspect import getargspec
from .http import HttpException, Request, Response
from ..utils.storage import VersionedStorage
from .url import URL


logger = logging.getLogger(__name__)


def prepare_handler(handler):
    '''Wrapps functions, that they can be usual WebHandler's'''
    if type(handler) in (types.FunctionType, types.MethodType):
        handler = FunctionWrapper(handler)
    return handler


def process_http_exception(response, e):
    response.status = e.status
    if e.status in (httplib.MOVED_PERMANENTLY,
                    httplib.SEE_OTHER):
        if isinstance(e.url, unicode):
            url = e.url.encode('utf-8')
        else:
            url = str(e.url)
        response.headers.add('Location', url)



class WebHandler(object):
    '''Base class for all request handlers.'''

    def __or__(self, next_handler):
        if hasattr(self, '_next_handler'):
            self._next_handler | next_handler
        else:
            self._next_handler = prepare_handler(next_handler)
        return self

    def handle(self, env, data, next_handler):
        '''This method should be overridden in subclasses.'''
        return next_handler(env, data)

    def trace(self, tracer):
        next_handler = self.get_next()
        # if next_handler is lambda - the end of chain
        if not type(next_handler) is types.FunctionType:
            next_handler.trace(tracer)

    def __repr__(self):
        return '%s()' % self.__class__.__name__

    def __call__(self, env, data):
        next_handler = self.get_next()
        env._commit()
        data._commit()
        result = self.handle(env, data, next_handler)
        if result is None:
            if env._modified:
                env._rollback()
            if data._modified:
                data._rollback()
        return result

    def get_next(self):
        if hasattr(self, '_next_handler'):
            return self._next_handler
        #XXX: may be FunctionWrapper?
        return lambda e, d: None

    def as_wsgi(self):
        def wrapper(environ, start_response):
            env = VersionedStorage()
            env.request = Request(environ)
            data = VersionedStorage()
            try:
                response = self(env, data)
                if response is None:
                    logger.debug('Application returned None instead of Response object')
                    status_int = httplib.NOT_FOUND
                    response = Response(status=status_int, 
                                        body='%d %s' % (status_int, httplib.responses[status_int]))
            except HttpException, e:
                response = Response()
                process_http_exception(response, e)
                status_int = response.status_int
                response.write('%d %s' % (status_int, httplib.responses[status_int]))
            except Exception, e:
                logger.exception(e)
                raise

            headers = response.headers.items()
            start_response(response.status, headers)
            return [response.body]
        return wrapper


class Reverse(object):

    def __init__(self, urls, env=None):
        self.urls = urls
        self.env = env

    @property
    def namespace(self):
        if self.env:
            return 'namespace' in self.env and self.env.namespace or ''
        return ''

    def __call__(self, name, **kwargs):
        if name.startswith('.'):
            local_name = name.lstrip('.')
            up = len(name) - len(local_name) - 1
            if up != 0:
                ns = ''.join(self.namespace.split('.')[:-up])
            else:
                ns = self.namespace
            name = ns + '.' + local_name

        subdomains, builders = self.urls[name]

        host = u'.'.join(subdomains)
        # path - urlencoded str
        path = ''.join([b(**kwargs) for b in builders])
        return URL(path, host=host)

    @classmethod
    def from_handler(cls, handler, env=None):
        tracer = Tracer()
        handler.trace(tracer)
        return cls(tracer.urls, env=env)


class cases(WebHandler):

    def __init__(self, *handlers, **kwargs):
        self.handlers = []
        for handler in handlers:
            self.handlers.append(prepare_handler(handler))

    def __or__(self, next_handler):
        'cases needs to set next handler for each handler it keeps'
        for handler in self.handlers:
            handler | prepare_handler(next_handler)
        return self

    def handle(self, env, data, next_handler):
        for handler in self.handlers:
            result = handler(env, data)
            if result is None:
                continue
            return result

    def trace(self, tracer):
        for handler in self.handlers:
            handler.trace(tracer)
        super(cases, self).trace(tracer)

    def __repr__(self):
        return '%s(*%r)' % (self.__class__.__name__, self.handlers)


class FunctionWrapper(WebHandler):
    '''Wrapper for handler represented by function'''

    def __init__(self, func):
        self.func = func

    def handle(self, env, data, next_handler):
        return self.func(env, data, next_handler)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.func.__name__)


handler = FunctionWrapper


class Tracer(object):

    def __init__(self):
        self.__urls = {}
        self._current_step = {}

    @property
    def urls(self):
        return self.__urls

    def check_name(self, name):
        if name in self.__urls:
            raise ValueError('Dublicating key "%s" in url map' % name)

    def finish_step(self):
        # get subdomains, namespaces if there are any
        subdomains = self._current_step.get('subdomain', [])
        subdomains.reverse()
        namespaces = self._current_step.get('namespace', [])

        # get url name and url builders if there are any
        url_name = self._current_step.get('url_name', None)
        builders = self._current_step.get('builder', [])
        nested_list = self._current_step.get('nested_list', None)

        # url name show that it is an usual chain (no nested map)
        if url_name:
            url_name = url_name[0]
            if namespaces:
                url_name = '.'.join(namespaces) + '.' + url_name
            self.check_name(url_name)
            self.__urls[url_name] = (subdomains, builders)
        # nested map (which also may have nested maps)
        elif nested_list:
            nested_list = nested_list[0]
            for k,v in nested_list.urls.items():
                if namespaces:
                    k = '.'.join(namespaces) + '.' + k
                self.check_name(k)
                self.__urls[k] = (v[0] + subdomains, builders + v[1])

        self._current_step = {}

    def __getattr__(self, name):
        return lambda e: self._current_step.setdefault(name, []).append(e)
