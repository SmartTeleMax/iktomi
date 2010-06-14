# -*- coding: utf-8 -*-

__all__ = ['RequestHandler', 'STOP', 'Map']

import logging
import types
import httplib
from inspect import getargspec
from .http import HttpException, Request, CopyOnUpdateDict, Response
from ..utils.url import URL


logger = logging.getLogger(__name__)


def prepare_handler(handler):
    '''Wrappes functions, that they can be usual RequestHandler's'''
    if type(handler) in (types.FunctionType, types.MethodType):
        handler = FunctionWrapper(handler)
    return handler


def map_row_from_handler(h):
    if isinstance(h, Map) and len(h.grid) == 1:
        return h.grid[0]
    else:
        return [h]


class STOP(object): pass


class RequestHandler(object):
    '''Base class for all request handlers.'''

    def __or__(self, next_):
        next_ = prepare_handler(next_)
        return Map(initial_grid=[[self] + map_row_from_handler(next_)])

    def __call__(self, rctx):
        logger.debug('Handled by %r' % self)
        return self.handle(rctx)

    def handle(self, rctx):
        '''This method should be overridden in subclasses.
        It always takes rctx object as only argument and returns it'''
        return rctx.next()

    def trace(self, tracer):
        pass

    def __repr__(self):
        return '%s()' % self.__class__.__name__


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

        host = u'.'.join(subdomains)
        absolute = (host != self.host)
        path = u''.join([b(**kwargs) for b in builders])
        return URL(path, host=host)


class Map(RequestHandler):

    def __init__(self, *handlers, **kwargs):
        self.grid = kwargs.pop('initial_grid', [])
        for handler in handlers:
            handler = prepare_handler(handler)
            row = map_row_from_handler(handler)
            self.grid.append(row)
        if not self.grid:
            # length of grid must be at least 1
            self.grid.append([])
        self.__urls = self.compile_urls_map()

    def __or__(self, next_):
        next_ = prepare_handler(next_)
        row = map_row_from_handler(next_)
        if len(self.grid) == 1:
            return Map(initial_grid=[self.grid[0] + row])
        return Map(initial_grid=[[self] + row])

    @property
    def urls(self):
        return self.__urls

    def handle(self, rctx):
        logger.debug('Map begin %r' % self)

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

        for i in xrange(len(self.grid)):
            rctx.lazy_copy()
            result = self.run_handler(rctx, i, 0)
            if result is not STOP:
                result.commit()
                return result.next()
            rctx.rollback()
        return STOP

    def run_handler(self, rctx, i, j):
        logger.debug('Position in map: %s %s' % (i, j))
        try:
            handler = self.grid[i][j]
        except IndexError:
            return rctx
        else:
            rctx._set_map_state(self, i, j+1)
            return handler(rctx)

    def compile_urls_map(self):
        tracer = Tracer()
        for row in self.grid:
            for item in row:
                if isinstance(item, Map):
                    tracer.nested_map(item)
                    break
                item.trace(tracer)
            tracer.finish_step()
        return tracer.urls

    def __repr__(self):
        return '%s(*%r)' % (self.__class__.__name__, self.grid)


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
        arg_offset = 1 if type(self.func) is types.MethodType else 0
        if argsspec.defaults and len(argsspec.defaults) > 0:
            args = argsspec.args[arg_offset:-len(argsspec.defaults)]
            kwargs = {}
            for i, kwarg_name in enumerate(argsspec.args[-len(argsspec.defaults):]):
                if kwarg_name in rctx.data:
                    kwargs[kwarg_name] = rctx.data[kwarg_name]
                else:
                    kwargs[kwarg_name] = argsspec.defaults[i]
        else:
            args = argsspec.args[arg_offset:]
            kwargs = {}
        # form list of arguments values
        args = [rctx] + [rctx.data[arg_name] for arg_name in args[1:]]
        result = self.func(*args, **kwargs)
        if result is STOP:
            return STOP
        if isinstance(result, dict):
            rctx.data.update(result)
        return rctx.next()

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


class RequestContext(object):
    '''
    Context of the request. A class containing request and response objects and
    a number of data containers with request environment and processing data.
    '''

    def __init__(self, wsgi_environ):
        self.request = Request(environ=wsgi_environ, charset='utf8')
        self.response = Response()
        self.wsgi_env = wsgi_environ.copy()

        #: this attribute is for views and template data,
        #: for example filter match appends params here.
        self.data = CopyOnUpdateDict()

        #: this is config, static, declarative (key, value)
        self.conf = CopyOnUpdateDict(namespace='')

        #: this storage is for nesecary objects like db session, templates env,
        #: cache, url_for. something like dynamic config values.
        self.vals = CopyOnUpdateDict()
        # XXX it's big question, which dicts we have to commit after map success
        self._local = CopyOnUpdateDict()

    @classmethod
    def blank(cls, url, **data):
        '''
        Method returning blank rctx. Very useful for testing

        `data` - POST parameters.
        '''
        POST = data or None
        env = Request.blank(url, POST=POST).environ
        return cls(env)

    def _set_map_state(self, _map, i, j):
        v = self._local
        v['_map'], v['_map_i'], v['_map_j'] = _map, i, j

    def next(self):
        v = self._local
        if '_map' in self._local:
            return v._map.run_handler(self, v._map_i, v._map_j)
        return self

    def _dict_action(self, action):
        for d in self.data, self.vals, self.conf:
            getattr(d, action)()

    def lazy_copy(self):
        self._dict_action('lazy_copy')
        self._local.lazy_copy()

    def commit(self):
        self._dict_action('commit')
        self._local.rollback()

    def rollback(self):
        self._dict_action('rollback')
        self._local.rollback()

    def stop(self):
        return STOP

