# -*- coding: utf-8 -*-

__all__ = ['Application', 'AppEnvironment']

import logging
from iktomi.utils.storage import VersionedStorage, StorageFrame
from webob.exc import HTTPException, HTTPInternalServerError, \
                      HTTPNotFound
from .http import Request, RouteState
from .reverse import Reverse

logger = logging.getLogger(__name__)


class AppEnvironment(StorageFrame):

    def __init__(self, request, root, _parent_storage=None, **kwargs):
        StorageFrame.__init__(self, _parent_storage=_parent_storage, **kwargs)
        self.request = request
        self.root = root.bind_to_request(request)
        self._route_state = RouteState(request)


class Application(object):

    EnvCls = AppEnvironment

    def __init__(self, handler, EnvCls=None):
        self.handler = handler
        self.EnvCls = EnvCls or AppEnvironment
        self.root = Reverse.from_handler(handler)

    def get_response(self, env, data):
        try:
            response = self.handler(env, data)
            if response is None:
                logger.debug('Application returned None '
                             'instead of Response object')
                response = HTTPNotFound()
        except HTTPException, e:
            response = e
        except Exception, e:
            logger.exception(e)
            response = HTTPInternalServerError()
        return response

    def __call__(self, environ, start_response):
        request = Request(environ, charset='utf-8')
        env = VersionedStorage(self.EnvCls, request, self.root)
        data = VersionedStorage()
        response = self.get_response(env, data)
        return response(environ, start_response)
