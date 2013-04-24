# -*- coding: utf-8 -*-
""" New implementation of cache handler.
XXX: Before marge to cache.py lets test as separate module for
     a while for testing and fast rollback

Supports two types of cache:
* Cache class is for basic cache that stores only content
* CachedWithContentType is for cache with content type (as separate cache key)
"""

__all__ = ['Cached', 'CachedWithContentType', 'CachedWithContentType']

from iktomi import web
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Set to INFO explicitly to see messages


class Cached(web.WebHandler):
    """ WebHandler that caches all GET and HEAD requests, stores them in
    env.cache.
    Store in format that compatible with nginx MemCached.
    Usage example
    >>> app = web.request_filter(environment) |\
    ...     Cached(content_type='text/xml') | web.cases()

    Headers are ignored.
    """

    def __init__(self, duration=None, content_type='text/html'):
        """ Contructor
        :param content_type:
          Content type set to header when load from cache.
        :type content_type: string
        """
        self.duration = duration
        self.content_type = content_type

    def get_cache_name(self, env):
        return env.request.url

    def get_duration(self, env):
        if self.duration is None:
            return env.cfg.DEFAULT_CACHE_DURATION
        elif isinstance(self.duration, basestring):
            return env.cfg.CACHE_DURATIONS.get(
                self.duration,
                env.cfg.DEFAULT_CACHE_DURATION)
        else:
            return self.duration

    def save_response_to_cache(self, env, response, duration):
        """ Save response to cache without guaranty
        """
        content = response.body
        cache_name = self.get_cache_name(env)
        if len(cache_name)>250:
            return None
        logger.info('Caching for %i seconds %s', duration, cache_name)
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        env.cache.set(cache_name, content, time=duration)

    def get_response_from_cache(self, env):
        cache_name = self.get_cache_name(env)
        if len(cache_name)>250:
            return None
        body = env.cache.get(cache_name)
        logger.info('Getting from cache. Got %s',
                    (body if body is None else type(body)))
        if body is None:
            return None
        logger.info('Got from cache by `%s`', cache_name)
        return web.Response(body, content_type=self.content_type)

    def call_view(self, env, data):
        logger.info("Call view %s", env.request.url)
        response = self.next_handler(env, data)
        if response is not None:
            duration = self.get_duration(env)
            self.save_response_to_cache(env, response, duration)
            return response
        return None

    def cache(self, env, data):
        enabled = getattr(env.cfg, 'CACHE_PAGES_ENABLED', True)
        if not enabled or env.request.method not in ('GET', 'HEAD'):
            response = self.next_handler(env, data)
            logger.info("Cache skipped")
            return response

        cached = self.get_response_from_cache(env)
        if not cached:
            cached = self.call_view(env, data)
            if cached is None:
                return None

        return cached
    __call__ = cache


class CachedWithContentType(Cached):
    """ Cahce WebHandler that supports content-type header caching in
    special format. Not compatible with nginx
    """

    def __init__(self, duration=None, content_type='text/html'):
        """ Contructor
        content_type used as default CT when CT-header is epsend in response
        """
        self.duration = duration
        self.content_type = content_type

    def get_cache_name(self, env):
        return env.request.url

    def save_response_to_cache(self, env, response, duration):
        content = response.body
        cache_name = self.get_cache_name(env)
        if len(cache_name)>248:
            return None
        logger.info('Caching body for %i seconds %s', duration, cache_name)
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        env.cache.set(cache_name, content, time=duration)
        content_type = response.headers.getall('content-type')
        if not content_type:
            content_type = self.content_type
        else:
            content_type = content_type[0]
        logger.info('Caching Content-Type `%s` for %i seconds %s', content_type,
                    duration, cache_name)
        env.cache.set('ct:' + cache_name, content_type, time=duration)

    def get_response_from_cache(self, env):
        cache_name = self.get_cache_name(env)
        if len(cache_name)>248:
            return None
        body = env.cache.get(cache_name)
        content_type = None
        if body:  # XXX: If body
            content_type = env.cache.get('ct:' + cache_name)
        logger.info('Got from cache: %s , Content-Type: %s',
                    (body if body is None else type(body)), content_type, )
        if body is None or content_type is None:
            return None
        return web.Response(body, content_type=content_type)


def cache(duration=None, content_type='text/html'):
    """ Cache decorator for views functions """
    def decor(view):
        h = Cached(duration, content_type=content_type) | view
        if hasattr(view, 'func_name'):
            h.func_name = view.func_name
        return h
    return decor
