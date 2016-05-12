# -*- coding: utf-8 -*-

__all__ = ['WebHandler', 'cases', 'request_filter']

import logging
import functools

from copy import copy
from webob import Response

logger = logging.getLogger(__name__)


def is_chainable(handler):
    while isinstance(handler, WebHandler):
        if not hasattr(handler, '_next_handler'):
            return True
        handler = handler._next_handler
    return False

def respond(response):
    def response_wrapper(env, data):
        return response
    return response_wrapper

def prepare_handler(handler):
    if isinstance(handler, Response):
        return respond(handler)
    elif isinstance(handler, type) and \
         issubclass(handler, Response):
        return respond(handler())
    return handler


class WebHandler(object):
    '''Base class for all request handlers.'''

    def __or__(self, next_handler):
        '''
        Supports chaining handler after itself::

            WebHandlerSubclass() | another_handler
        '''
        # XXX in some cases copy count can be big
        #     for example, chaining something after a huge cases(..) handler
        #     causes a copy of each single nested handler.
        #     Sure, is bad idea to chain anything after big cases(..) anyway.
        h = self.copy()

        next_handler = prepare_handler(next_handler)
        if hasattr(self, '_next_handler'):
            h._next_handler = h._next_handler | next_handler
        else:
            h._next_handler = next_handler
        return h

    def _locations(self):
        next_handler = self.next_handler
        if isinstance(next_handler, WebHandler):
            return next_handler._locations()
        # we are last in chain
        return {}

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)

    def __call__(self, env, data):
        '''
        Subclasses should define __call__ with handler code. It is good style to
        give a name similar to handler's name to method and then make an alias
        to __call__::

            class MyHandler(WebHandler):

                def my_handler(self, env, data):
                    do_something(env, data)
                    return self.next_handler(env, data)
                __call__ = my_handler  # This method should be overridden 
                                       # in subclasses.
        '''
        raise NotImplementedError(
                '__call__ is not implemented in {!r}'.format(self))

    @property
    def next_handler(self):
        '''A handler, chained next to self'''
        if hasattr(self, '_next_handler'):
            return self._next_handler
        return lambda e, d: None

    def copy(self):
        '''
        Returns copy for the handler to make handlers reusable.
        Handlers are being copied automatically on chaining,
        so you do not need to do it manually.'''
        return copy(self)


class cases(WebHandler):
    # XXX bad docstring
    '''
    Handler incapsulating multiple routing branches and choosing one of them
    that matches current request::

        web.cases(
            web.match('/', 'index') | index,
            web.match('/contacts', 'contacts') | contacts,
            web.match('/about', 'about') | about,
        )'''

    def __init__(self, *handlers):
        self.handlers = [prepare_handler(x) for x in handlers]

    def __or__(self, next_handler):
        #cases needs to set next handler for each handler it keeps
        h = self.copy()
        h.handlers = [(handler | next_handler
                            if is_chainable(handler) 
                            else handler)
                      for handler in self.handlers]
        return h

    def cases(self, env, data):
        '''Calls each nested handler until one of them returns nonzero result.

        If any handler returns `None`, it is interpreted as 
        "request does not match, the handler has nothing to do with it and 
        `web.cases` should try to call the next handler".'''
        for handler in self.handlers:
            env._push()
            data._push()
            try:
                result = handler(env, data)
            finally:
                env._pop()
                data._pop()
            if result is not None:
                return result
    # for readable tracebacks
    __call__ = cases

    def _locations(self):
        locations = {}
        for handler in self.handlers:
            if isinstance(handler, WebHandler):
                handler_locations = handler._locations()
                for k, v in handler_locations.items():
                    if k in locations:
                        raise ValueError(
                                'Location "{}" already exists'.format(k))
                    locations[k] = v
        return locations

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               ', '.join(repr(h) for h in self.handlers))


class _FunctionWrapper3(WebHandler):
    '''
    Wrapper for handler represented by function 
    (3 args, old-style)
    '''

    def __init__(self, func):
        self.handler = func

    def function_wrapper(self, env, data):
        return self.handler(env, data, self.next_handler)
    __call__ = function_wrapper

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.handler)


def request_filter(func):
    '''Decorator transforming function to regular WebHandler.
    This allows to chain other handlers after given.
    The next handler is passed as third argument into the wrapped function::

        @web.request_filter
        def wrapper(env, data, next_handler):
            do_something()
            result = next_handler(env, data)
            return do_something_else(result)

        wrapped_app = wrapper | handler
        '''
    return functools.wraps(func)(_FunctionWrapper3(func))

