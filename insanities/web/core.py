# -*- coding: utf-8 -*-

__all__ = ['RequestHandler', 'ContinueRoute', 'Tracer', 'Map', 'Wrapper']

import logging
import types
import httplib
from inspect import getargspec
from .http import HttpException, RequestContext


logger = logging.getLogger(__name__)


class InvalidChaining(Exception): pass

class ContinueRoute(Exception):

    @property
    def who(self):
        return self.args[0]

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.who)


class RequestHandler(object):

    def handle(self, rctx):
        raise NotImplementedError()

    def trace(self, tracer):
        tracer.handler(self)

    def __or__(self, next):
        '''
        >>> r1 = RequestHandler()
        >>> r2 = RequestHandler()
        >>> r3 = RequestHandler()
        >>> chain = r1 | r2 | r3
        >>> r1 in chain.handlers
        True
        >>> r2 is chain.handlers[1]
        True
        >>> r3 is chain.handlers[2]
        True
        '''
        if isinstance(next, Wrapper):
            raise InvalidChaining('Left chaining to Wrapper is disallowed')

        if type(next) in (types.FunctionType, types.LambdaType):
            next = FunctionWrapper(next)
        if isinstance(next, Chain):
            next.append(self, first=True)
            return next
        return Chain(self, next)

    __rshift__ = __or__

    def __call__(self, rctx):
        return self.handle(rctx)

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class Chain(object):

    def __init__(self, *handlers):
        self.__handlers = list(handlers)
        
        maps = filter(lambda x: isinstance(x, Map), handlers)
        if len(maps) > 1:
            raise InvalidChaining('Only one Map is allowed in chain')

    def __call__(self, rctx):
        for handler in self.handlers:
            rctx = handler(rctx)
        return rctx

    def trace(self, tracer):
        for handler in self.handlers:
            # is handler nested map?
            if isinstance(handler, Map):
                # Append it to our tracer.
                tracer.append(handler)
            else:
                handler.trace(tracer)
        tracer.finish_step()

    @property
    def handlers(self):
        return self.__handlers

    def url_for(self, url_name_, **kwargs):
        # Delegate url_for for the Map handler
        # XXX store Map separately?
        return self.instance(Map).url_for(url_name_, **kwargs)

    @property
    def rctx_class(self):
        # Delegate url_for for the Map handler
        return self.instance(Map).rctx_class
        

    def __or__(self, next):
        if isinstance(next, Wrapper):
            raise InvalidChaining('Left chaining to Wrapper is disallowed')
        if isinstance(next, Map):
            if self.instances(Map):
                # we are not shure if url reverse and other functions
                # are working properli in this case
                raise InvalidChaining('Only one Map is allowed in chain')
        
        if isinstance(next, self.__class__):
            self.__handlers += next.handlers
        else:
            if type(next) in (types.FunctionType, types.LambdaType):
                next = FunctionWrapper(next)
            self.__handlers.append(next)
        return self

    def append(self, handler, first=False):
        if first:
            self.__handlers.insert(0, handler)
        else:
            self.__handlers.append(handler)

    def __len__(self):
        return len(self.__handlers)

    def __contains__(self, cls):
        '''
        Check if cls instances are in handlers list
        '''
        for handler in self.__handlers:
            if isinstance(handler, cls):
                return True
        return False

    def instance(self, cls):
        for handler in self.__handlers:
            if isinstance(handler, cls):
                return handler
        raise ValueError('"%s" not found in chain' % cls)

    def instances(self, cls):
        result = []
        for handler in self.__handlers:
            if isinstance(handler, cls):
                result.append(handler)
        return result

    def __repr__(self):
        return '%s(*%r)' % (self.__class__.__name__, self.__handlers)


class FunctionWrapper(RequestHandler):
    '''Wrapper for handler represented by function'''
    def __init__(self, func):
        super(FunctionWrapper, self).__init__()
        self.func = func

    def handle(self, rctx):
        # Now we will find which arguments are required by
        # wrapped function. And then get arguments values from rctx data,
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
            rctx.add_data(**result)
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


class Map(RequestHandler):
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


class Wrapper(RequestHandler):
    '''
    Wrappers can be used only as first elements of chain.
    Unlike other RequestHandlers, wrappers are not
    '''

    def __init__(self):
        super(Wrapper, self).__init__()
        self.next = None
        self.prev = None
        self._last_wrapper = self # only for chaining
        #self._handler = None

    def handle(self, rctx):
        raise NotImplemented
    
    def url_for(self, url_name_, **kwargs):
        # Delegate url_for for the first handler
        return self._last_wrapper.next.url_for(url_name_, **kwargs)

    @property
    def rctx_class(self):
        # Delegate url_for for the first handler
        return self._last_wrapper.next.rctx_class

    def __or__(self, next):
        '''
        Test cases::
        
            W|W
            W|(W|W)
            W|(W|W|H)
            W|H|W - raises exception
            H|W - raises eception
            W|W|H|H
        '''
        handler = self._last_wrapper.next
        
        if isinstance(next, Wrapper):
            if handler is not None:
                raise InvalidChaining(u'Attempt to chain wrapped handler with'
                                      'wrapper')
            if next.prev is not None:
                raise InvalidChaining(u'wrapper can be used once')
                
            self.next = next
            next.prev = self
            self._last_wrapper = next._last_wrapper
        else:
            if handler is not None:
                next = handler | next
            
            self._last_wrapper.next = next
        return self

    __rshift__ = __or__

    
