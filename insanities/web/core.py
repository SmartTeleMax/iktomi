# -*- coding: utf-8 -*-

__all__ = ['WebHandler', 'cases', 'handler', 'locations']

import logging
import types
import httplib
import functools
from webob.exc import HTTPException
from .http import Request, Response, RouteState
from ..utils.storage import VersionedStorage
from .reverse import URL


logger = logging.getLogger(__name__)


def prepare_handler(handler):
    '''Wrapps functions, that they can be usual WebHandler's'''
    if type(handler) in (types.FunctionType, types.MethodType):
        handler = wrap_function(handler)
    return handler


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

    def _locations(self):
        next_handler = self.get_next()
        # if next_handler is lambda - the end of chain
        if not type(next_handler) is types.FunctionType:
            return next_handler._locations()
        # we are last in chain
        return {}

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
        #XXX: may be _FunctionWrapper?
        return lambda e, d: None

    def as_wsgi(self):
        def wsgi(environ, start_response):
            env = VersionedStorage()
            env.request = Request(environ, charset='utf-8')
            env._route_state = RouteState(env.request)
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

            headers = response.headers.items()
            start_response(response.status, headers)
            return [response.body]
        return wsgi


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

    def _locations(self):
        locations = {}
        for handler in self.handlers:
            handler_locations = handler._locations()
            for k, v in handler_locations.items():
                if k in locations:
                    raise ValueError('Location "%s" already exists' % k)
                locations[k] = v
        return locations

    def __repr__(self):
        return '%s(*%r)' % (self.__class__.__name__, self.handlers)


class _FunctionWrapper(WebHandler):
    '''Wrapper for handler represented by function'''

    def __init__(self, func):
        self.handle = func

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.handle.__name__)


def wrap_function(func):
    return functools.wraps(func)(_FunctionWrapper(func))


handler = wrap_function


def locations(handler):
    return handler._locations()
