# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)


from insanities.web.core import RequestHandler


class local_cache_env(RequestHandler):
    '''
    This class implements simple cache interface API.
    Only for development purpose.
    '''

    def __init__(self, name='session_storage'):
        super(local_cache_env, self).__init__()
        self.cache = {}
        self.name = name

    def handle(self, rctx):
        rctx.vals[self.name] = self
        return rctx

    def get(self, key):
        logger.debug('cache: get(%s)' % key)
        return self.cache.get(key)

    def set(self, key, value):
        logger.debug('cache: set(%r, %r)' % (key, value))
        self.cache[key] = value
        return True

    def delete(self, key):
        logger.debug('cache: delete(%r)' % key)
        if key in self.cache:
            try:
                del self.cache[key]
            except KeyError:
                pass
        return True


class memcache_env(RequestHandler):
    '''
    This class wrapps all invocations of memcache.Client methods.
    Only for development purpose.
    '''

    def __init__(self, hosts, name='session_storage'):
        super(memcache_env, self).__init__()
        from memcache import Client
        self.cache = Client(hosts)
        self.name = name

    def handle(self, rctx):
        rctx.vals[self.name] = self.cache
        return rctx
