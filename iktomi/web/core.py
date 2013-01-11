# -*- coding: utf-8 -*-

__all__ = ['WebHandler', 'cases', 'locations', 'request_filter', 
           'AppEnvironment']

import logging
import types
import httplib
import functools
from webob.exc import HTTPException
from .http import Request, Response, RouteState
from iktomi.utils.storage import VersionedStorage, StorageFrame

from copy import copy

logger = logging.getLogger(__name__)


def is_chainable(handler):
    while isinstance(handler, WebHandler):
        if not hasattr(handler, '_next_handler'):
            return True
        handler = handler._next_handler
    return False

class AppEnvironment(StorageFrame):

    def __init__(self, request, root, _parent_storage=None, **kwargs):
        StorageFrame.__init__(self, _parent_storage=_parent_storage, **kwargs)
        self.request = request
        self.root = root.bind_to_request(request)
        self._route_state = RouteState(request)


class WebHandler(object):
    '''Base class for all request handlers.'''

    EnvCls = AppEnvironment

    def __or__(self, next_handler):
        # XXX copy count depends on chain length geometrically!
        h = self.copy()
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
        return '%s()' % self.__class__.__name__

    def __call__(self, env, data):
        '''This method should be overridden in subclasses.'''
        raise NotImplementedError("__call__ is not implemented in %r" % self)

    @property
    def next_handler(self):
        if hasattr(self, '_next_handler'):
            return self._next_handler
        return lambda e, d: None

    def copy(self):
        # to make handlers reusable
        return copy(self)

    def as_wsgi(self, EnvCls=None):
        from .reverse import Reverse
        root = Reverse.from_handler(self)
        EnvCls = EnvCls or self.EnvCls
        def wsgi(environ, start_response):
            request = Request(environ, charset='utf-8')
            env = VersionedStorage(EnvCls, request, root)
            data = VersionedStorage()
            try:
                response = self(env, data)
                if response is None:
                    logger.debug('Application returned None '
                                 'instead of Response object')
                    status_int = httplib.NOT_FOUND
                    response = Response(status=status_int, 
                                        body='%d %s' % (status_int, 
                                                        httplib.responses[status_int]))
            except HTTPException, e:
                response = e
            except Exception, e:
                logger.exception(e)
                raise

            return response(environ, start_response)
        return wsgi


class cases(WebHandler):

    def __init__(self, *handlers, **kwargs):
        self.handlers = []
        for handler in handlers:
            self.handlers.append(handler)

    def __or__(self, next_handler):
        'cases needs to set next handler for each handler it keeps'
        h = self.copy()
        h.handlers = [(handler | next_handler
                            if is_chainable(handler) 
                            else handler)
                      for handler in self.handlers]
        return h

    def cases(self, env, data):
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
                        raise ValueError('Location "%s" already exists' % k)
                    locations[k] = v
        return locations

    def __repr__(self):
        return '%s(*%r)' % (self.__class__.__name__, self.handlers)


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
        return '%s(%r)' % (self.__class__.__name__, self.handler)


def request_filter(func):
    return functools.wraps(func)(_FunctionWrapper3(func))


def locations(handler):
    return handler._locations()
