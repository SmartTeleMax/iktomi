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
        return rctx

    def next(self):
        return self._next_handler

    def trace(self, tracer):
        tracer.handler(self)

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


class Map(RequestHandler):

    def __init__(self, *handlers, **kwargs):
        super(Map, self).__init__()
        # make sure all views are wrapped
        self.handlers = [prepaire_handler(h) for h in handlers]

    def handle(self, rctx):
        logger.debug('Map begin %r' % self)
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
        # all handlers raised ContinueRoute
        raise ContinueRoute(self)

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
        #TODO: check for correct chain members order
        # get prefixes, namespaces if there are any
        prefixes = self._current_step.get('prefix', [])
        namespaces = self._current_step.get('namespace', [])

        # get url name and url builder if there are any
        url_name = self._current_step.get('url_name', None)
        builder = self._current_step.get('builder', None)
        handlers = self._current_step.get('handler', [])

        append = self._current_step.get('append', None)

        # url name show that it is an usual chain (no nested map)
        if url_name:
            url_name = url_name[0]
            if namespaces:
                url_name = '.'.join(namespaces) + '.' + url_name
            self.check_name(url_name)
            self.__urls[url_name] = [prefixes, builder[0], handlers]
        # nested map (which also may have nested maps)
        elif append:
            nested_map = append[0]
            for k,v in nested_map.urls.items():
                if namespaces:
                    namespace = '.'.join(namespaces)
                    nested_map.set_namespace(namespace)
                    k = namespace + '.' + k
                v = [prefixes + v[0], v[1], v[2] + handlers]
                self.check_name(k)
                self.__urls[k] = v

        self._current_step = {}

    def __getattr__(self, name):
        return lambda e: self._current_step.setdefault(name, []).append(e)


class OldMap(RequestHandler):
    '''
    '''

    def __init__(self, *chains, **kwargs):
        super(Map, self).__init__()
        self.chains = []
        self._namespace = ''
        self.rctx_class = kwargs.get('rctx_class', RequestContext)
        # lets walk through chains and check them
        for chain in chains:
            if type(chain) in (types.FunctionType, types.LambdaType):
                chain = FunctionWrapper(chain)
            self.chains.append(chain)
        # now we will trace all map to get urls dict
        self._urls = self.trace().urls

    def set_namespace(self, namespace):
        self._namespace = namespace

    @property
    def namespace(self):
        return self._namespace

    def trace(self, **kwargs):
        tracer = Tracer(**kwargs)
        for chain in self.chains:
            if isinstance(chain, self.__class__):
                tracer.append(chain)
                tracer.finish_step()
            else:
                chain.trace(tracer)
        return tracer

    def handle(self, rctx):
        logger.debug('Handle the path -- %s | qs -- %s' % (rctx.request.path, rctx.request.GET))
        from .filters import prefix
        
        if rctx._main_map is None:
            rctx._main_map = self
        
        for chain in self.chains:
            try:
                rctx = chain(rctx)
            except ContinueRoute, e:
                logger.debug('ContinueRoute by %r', e.who)
                # if prefixed nested map ask to continue?
                if isinstance(e.who, self.__class__) \
                and isinstance(chain, Chain) \
                and prefix in chain:
                    raise HttpException(httplib.NOT_FOUND)
                continue
            except HttpException, e:
                # here we process all HttpExceptions thrown by our chains
                rctx.response.status = e.status
                if e.status in (httplib.MOVED_PERMANENTLY,
                                httplib.SEE_OTHER):
                    rctx.response.headers['Location'] = e.url
                return rctx
            else:
                logger.debug('Matched chain "%r"' % chain)
                return rctx
        
        if rctx._main_map is self:
            rctx.response.status = httplib.NOT_FOUND
            return rctx
        raise ContinueRoute(self)

    @property
    def urls(self):
        return self._urls

    def url_for(self, url_name_, **kwargs):
        # if this map is nestead self.namespace will return full
        # namespace for this map
        url_name_ = self.namespace and self.namespace+'.'+url_name_ or url_name_
        # and now we ask the most parent map for prefixes and url builder
        prefixes, builder, handlers = self.urls[url_name_]
        return builder(prefixes, **kwargs)

    def __repr__(self):
        return '%s(*%r)' % (self.__class__.__name__, self.chains)
