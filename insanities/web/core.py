# -*- coding: utf-8 -*-

__all__ = ['RequestHandler', 'ContinueRoute', 'Map', 'Wrapper']

import logging
import types
import httplib
from inspect import getargspec
from .http import HttpException, RequestContext
from ..utils.url import URL


logger = logging.getLogger(__name__)


class ContinueRoute(Exception):

    @property
    def who(self):
        return self.args[0]

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.who)


def prepaire_handler(handler):
    '''Wrappes functions, that they can be usual RequestHandler's'''
    if type(handler) in (types.FunctionType, types.LambdaType):
        handler = FunctionWrapper(handler)
    return handler


def process_http_exception(rctx, e):
    rctx.response.status = e.status
    if e.status in (httplib.MOVED_PERMANENTLY,
                    httplib.SEE_OTHER):
        if isinstance(e.url, unicode):
            url = e.url.encode('utf-8')
        else:
            url = str(e.url)
        rctx.response.headers.add('Location', url)


class RequestHandler(object):
    '''
        Base class for all request handlers.
    '''


    def __init__(self):
        self._next_handler = None

    def __or__(self, next):
        if next is self:
            raise ValueError('You are chaining same object to it self "%s". '
                             'This causes max recursion error.' % next)
        if self._next_handler is None:
            self._next_handler = prepaire_handler(next)
        else:
            self._next_handler = self._next_handler | prepaire_handler(next)
        return self

    def __contains__(self, cls):
        next = self
        while next is not None:
            if next.__class__ is cls:
                return True
            next = next.next()
        return False

    def __call__(self, rctx):
        next = self
        while next is not None:
            logger.debug('Handled by %r' % next)
            rctx = next.handle(rctx)
            next = next.next()
        return rctx

    def handle(self, rctx):
        '''
        This method should be overridden in subclasses.

        It always takes rctx object as only argument and returns it
        '''
        return rctx

    def next(self):
        return self._next_handler

    def trace(self, tracer):
        pass

    def __repr__(self):
        result = '%s()' % self.__class__.__name__
        next = self.next()
        while next:
            result += ' | %r' % next
            next = next.next()
        return result

    def instances(self, cls):
        result = []
        for handler in self.__handlers:
            if isinstance(handler, cls):
                result.append(handler)
        return result


class Wrapper(RequestHandler):
    '''
    A subclass of RequestHandler with other order of calling chained handlers.

    Base class for handlers wrapping execution of next chains. Subclasses should
    execute chained handlers in :meth:`handle` method by calling :meth:`exec_wrapped`
    method. For example::

        class MyWrapper(Wrapper):
            def handle(self, rctx):
                do_smth(rctx)
                try:
                    rctx = self.exec_wrapped(rctx)
                finally:
                    do_smth2(rctx)
                return rctx

    *Note*: Be careful with exceptions. Chained method can throw exceptions including
    HttpExceptions. If you use wrappers to finalize some actions (close db connection,
    store http-sessions), it is recommended to use context managers
    ("with" statements) or try...finally constructions.
    '''
    def next(self):
        return None

    def exec_wrapped(self, rctx):
        '''Executes the wrapped chain. Should be called from :meth:`handle` method.'''
        next = self._next_handler
        while next is not None:
            logger.debug('Handled by %r' % next)
            try:
                rctx = next.handle(rctx)
            except ContinueRoute:
                break
            next = next.next()
        return rctx

    def handle(self, rctx):
        '''Should be overriden in subclasses.'''
        logger.debug("Wrapper begin %r" % self)
        rctx = self.exec_wrapped(rctx)
        logger.debug("Wrapper end %r" % self)
        return rctx

    def __repr__(self):
        return '%s() | %r' % (self.__class__.__name__, self._next_handler)


class Reverse(object):

    def __init__(self, urls, namespace, host=''):
        self.urls = urls
        self.namespace = namespace
        self.host = host

    def __call__(self, name, **kwargs):
        if self.namespace:
            local_name = self.namespace + '.' + name
            # if there are no url in local namespace, we search it in global
            url = self.urls.get(local_name) or self.urls[name]
        else:
            url = self.urls[name]

        subdomains, builders = url

        host = '.'.join(subdomains)
        absolute = (host != self.host)
        path = ''.join([b(**kwargs) for b in builders])
        return URL(path, host=host)


class Map(RequestHandler):

    def __init__(self, *handlers, **kwargs):
        super(Map, self).__init__()
        # make sure all views are wrapped
        self.handlers = [prepaire_handler(h) for h in handlers]
        self.__urls = self.compile_urls_map()
        self.rctx_class = kwargs.get('rctx_class', RequestContext)

    @property
    def urls(self):
        return self.__urls

    def handle(self, rctx):
        logger.debug('Map begin %r' % self)

        # put main map link to rctx
        if rctx.main_map is None:
            rctx.main_map = self

        # construct url_for
        last_url_for = getattr(rctx.vals, 'url_for', None)
        if last_url_for is None:
            urls = self.urls
        else:
            urls = last_url_for.urls
        # urls - url map of the most parent Map instance.
        # namespace is controlled by Conf wrapper instance,
        # so we just use rctx.conf.namespace
        url_for = Reverse(urls, rctx.conf.namespace,
                          host=rctx.request.host.split(':')[0])
        rctx.vals['url_for'] = rctx.data['url_for'] = url_for

        for i in xrange(len(self.handlers)):
            handler = self.handlers[i]
            try:
                rctx = handler(rctx)
            except ContinueRoute:
                pass
            except HttpException, e:
                # here we process all HttpExceptions thrown by our chains
                logger.debug('HttpException in map %r by "%s"' % (self, handler))
                process_http_exception(rctx, e)
                return rctx
            else:
                return rctx

        rctx.vals['url_for'] = rctx.data['url_for'] = last_url_for
        if rctx.main_map is self:
            return rctx
        # all handlers raised ContinueRoute
        raise ContinueRoute(self)

    def compile_urls_map(self):
        tracer = Tracer()
        for handler in self.handlers:
            item = handler
            while item:
                if isinstance(item, self.__class__):
                    tracer.nested_map(item)
                    break
                item.trace(tracer)
                item = item._next_handler
            tracer.finish_step()
        return tracer.urls

    def __repr__(self):
        return '%s(*%r)' % (self.__class__.__name__, self.handlers)


class FunctionWrapper(RequestHandler):
    '''Wrapper for handler represented by function'''

    def __init__(self, func):
        super(FunctionWrapper, self).__init__()
        self.func = func

    def handle(self, rctx):
        # Now we will find which arguments are required by
        # wrapped function. And then get arguments values from rctx
        # data,
        # if there is no value argument we trying to get default value
        # from function specification otherwise Exception is raised
        argsspec = getargspec(self.func)
        if argsspec.defaults and len(argsspec.defaults) > 0:
            args = argsspec.args[:-len(argsspec.defaults)]
            kwargs = {}
            for i, kwarg_name in enumerate(argsspec.args[-len(argsspec.defaults):]):
                if kwarg_name in rctx.data:
                    kwargs[kwarg_name] = rctx.data[kwarg_name]
                else:
                    kwargs[kwarg_name] = argsspec.defaults[i]
        else:
            args = argsspec.args
            kwargs = {}
        # form list of arguments values
        args = [rctx] + [rctx.data[arg_name] for arg_name in args[1:]]
        result = self.func(*args, **kwargs)
        if isinstance(result, dict):
            rctx.data.update(result)
        return rctx

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.func.__name__)


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
        nested_map = self._current_step.get('nested_map', None)

        # url name show that it is an usual chain (no nested map)
        if url_name:
            url_name = url_name[0]
            if namespaces:
                url_name = '.'.join(namespaces) + '.' + url_name
            self.check_name(url_name)
            self.__urls[url_name] = (subdomains, builders)
        # nested map (which also may have nested maps)
        elif nested_map:
            nested_map = nested_map[0]
            for k,v in nested_map.urls.items():
                if namespaces:
                    k = '.'.join(namespaces) + '.' + k
                self.check_name(k)
                self.__urls[k] = (v[0] + subdomains, builders + v[1])

        self._current_step = {}

    def __getattr__(self, name):
        return lambda e: self._current_step.setdefault(name, []).append(e)
