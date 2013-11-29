# -*- coding: utf-8 -*-

__all__ = ['Application', 'AppEnvironment']

import logging
from iktomi.utils.storage import VersionedStorage, StorageFrame, storage_property
from webob.exc import HTTPException, HTTPInternalServerError, \
                      HTTPNotFound
from webob import Request
from .route_state import RouteState
from .reverse import Reverse

logger = logging.getLogger(__name__)


class AppEnvironment(StorageFrame):

    def __init__(self, request, root, _parent_storage=None, **kwargs):
        StorageFrame.__init__(self, _parent_storage=_parent_storage, **kwargs)
        self.request = request
        self.root = root.bind_to_env(self._root_storage)
        self._route_state = RouteState(request)

    @storage_property
    def current_location(self):
        ns = getattr(self, 'namespace', '')
        url_name = getattr(self, 'current_url_name', '')
        return '.'.join(filter(None, (ns, url_name)))


class Application(object):

    env_class = AppEnvironment

    def __init__(self, handler, env_class=None):
        self.handler = handler
        if env_class is not None:
            self.env_class = env_class
        self.root = Reverse.from_handler(handler)

    def handle_error(self, env):
        logger.exception('Exception for %s %s :',
                         env.request.method, env.request.url)

    def handle(self, env, data):
        try:
            response = self.handler(env, data)
            if response is None:
                logger.debug('Application returned None '
                             'instead of Response object')
                response = HTTPNotFound()
        except HTTPException, e:
            response = e
        except Exception, e:
            self.handle_error(env)
            response = HTTPInternalServerError()
        return response

    def __call__(self, environ, start_response):
        request = Request(environ, charset='utf-8')
        env = VersionedStorage(self.env_class, request, self.root)
        data = VersionedStorage()
        response = self.handle(env, data)
        return response(environ, start_response)
