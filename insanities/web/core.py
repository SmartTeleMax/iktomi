# -*- coding: utf-8 -*-

__all__ = ['RequestHandler', 'ContinueRoute', 'Tracer', 'Map', 'Wrapper']

import logging
import types
import httplib
from inspect import getargspec
from .http import HttpException, RequestContext


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
        rctx.response.headers['Location'] = e.url


class RequestHandler(object):

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
        '''this method you should override in subclasses'''
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

    def next(self):
        return None

    def exec_wrapped(self, rctx):
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
        logger.debug("Wrapper begin %r" % self)
        rctx = self.exec_wrapped(rctx)
        logger.debug("Wrapper end %r" % self)
        return rctx

    def __repr__(self):
        return '%s() | %r' % (self.__class__.__name__, self._next_handler)


class Reverse(object):

    def __init__(self, urls, namespace):
        self.urls = urls
        self.namespace = namespace

    def __call__(self, name, **kwargs):
        #TODO: what if we need to provide absolute
        # url name and do not want namespace to be prepended
        if self.namespace:
            name = self.namespace + '.' + name
        prefixes, builder = self.urls[name]
        #TODO: return object insted of str
        return builder(prefixes, **kwargs)


class Map(RequestHandler):

    def __init__(self, *handlers, **kwargs):
        super(Map, self).__init__()
        # make sure all views are wrapped
        self.handlers = [prepaire_handler(h) for h in handlers]
        self.__urls = self.compile_urls_map()

    @property
    def urls(self):
        return self.__urls

    def handle(self, rctx):
        logger.debug('Map begin %r' % self)

        # put main map link to rctx
        if rctx.main_map is None:
            rctx.main_map = self

        # construct url_for
        last_url_for = getattr(rctx.conf, 'url_for', None)
        if last_url_for is None:
            urls = self.urls
        else:
            urls = last_url_for.urls
        # urls - url map of the most parent Map instance.
        # namespace is controlled by Conf wrapper instance,
        # so we just use rctx.conf.namespace
        url_for = Reverse(urls, rctx.conf.namespace)
        rctx.conf['url_for'] = url_for
        rctx.template_data['url_for'] = url_for

        handler = None
        for i in xrange(len(self.handlers)):
            try:
                handler = self.handlers[i]
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

        rctx.conf['url_for'] = last_url_for
        rctx.template_data['url_for'] = last_url_for
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
        # template_data,
        # if there is no value argument we trying to get default value
        # from function specification otherwise Exception is raised
        argsspec = getargspec(self.func)
        if argsspec.defaults and len(argsspec.defaults) > 0:
            args = argsspec.args[:-len(argsspec.defaults)]
            kwargs = {}
            for i, kwarg_name in enumerate(argsspec.args[-len(argsspec.defaults):]):
                if kwarg_name in rctx.template_data:
                    kwargs[kwarg_name] = rctx.template_data[kwarg_name]
                else:
                    kwargs[kwarg_name] = argsspec.defaults[i]
        else:
            args = argsspec.args
            kwargs = {}
        # form list of arguments values
        args = [rctx] + [rctx.template_data[arg_name] for arg_name in args[1:]]
        result = self.func(*args, **kwargs)
        if isinstance(result, dict):
            rctx.template_data.update(result)
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
        # get prefixes, namespaces if there are any
        prefixes = self._current_step.get('prefix', [])
        namespaces = self._current_step.get('namespace', [])

        # get url name and url builder if there are any
        url_name = self._current_step.get('url_name', None)
        builder = self._current_step.get('builder', None)
        nested_map = self._current_step.get('nested_map', None)

        # url name show that it is an usual chain (no nested map)
        if url_name:
            url_name = url_name[0]
            if namespaces:
                url_name = '.'.join(namespaces) + '.' + url_name
            self.check_name(url_name)
            self.__urls[url_name] = [prefixes, builder[0]]
        # nested map (which also may have nested maps)
        elif nested_map:
            nested_map = nested_map[0]
            for k,v in nested_map.urls.items():
                if namespaces:
                    k = '.'.join(namespaces) + '.' + k
                v = [prefixes + v[0], v[1]]
                self.check_name(k)
                self.__urls[k] = v

        self._current_step = {}

    def __getattr__(self, name):
        return lambda e: self._current_step.setdefault(name, []).append(e)
