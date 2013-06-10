# -*- coding: utf-8 -*-
""" New implementation of cache handler.
XXX: Before marge to cache.py lets test as separate module for
     a while for testing and fast rollback

Supports two types of cache:
* CacheManager class is for basic cache that stores only content
* CacheManagerWithContentType is for cache with content type (as separate cache key)
"""

__all__ = ['CacheManager', 'CacheManagerWithContentType', 'cache', 'nocache']

from iktomi import web
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Set to INFO explicitly to see messages


def nocache(handler):
    def wrap(*args, **kwargs):
        response = handler(*args, **kwargs)
        setattr(response, '_CACHE_ENABLED', False)
        return response
    return wrap


def cache(duration=None, content_type='text/html'):
    def decor(handler):
        def wrap(*args, **kwargs):
            response = handler(*args, **kwargs)
            setattr(response, '_CACHE_ENABLED', True)
            setattr(response, '_CACHE_DURATION', duration)
            setattr(response, '_CACHE_CONTENT_TYPE', content_type)
            return response
        return wrap
    return decor


class NocacheHandler(web.WebHandler):
    def __call__(self, env, data):
        return nocache(self.next_handler)(env, data)


class CacheHandler(web.WebHandler):
    def __init__(self, duration, content_type='text/html'):
        self._duration = duration
        self._content_type = content_type

    def __call__(self, env, data):
        return cache(self._duration, self._content_type)(self.next_handler)(env, data)


class CacheManager(web.WebHandler):
    _cache_name_length = 250

    def __init__(self, storage, default_duration, durations, content_type='text/html'):
        self._storage = storage
        self._default_duration = default_duration
        self._durations = durations
        self._content_type = content_type


    def get_cache_name(self, env):
        cache_name = env.request.url
        if len(cache_name) > self._cache_name_length:
            return None
        return cache_name

    def get_duration(self, response):
        if not getattr(response, '_CACHE_ENABLED', True):
            return None

        duration = getattr(response, '_CACHE_DURATION', self._default_duration)
        if isinstance(duration, int):
            return duration
        if duration in self._durations:
            return self._durations[duration]
        return self._default_duration

    def save_response_to_cache(self, env, response, duration):
        """ Save response to cache without guaranty
        """
        content = response.body
        cache_name = self.get_cache_name(env)
        if cache_name is None or duration is None:
            return None
        logger.info('Caching for %i seconds %s', duration, cache_name)
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        self._storage.set(cache_name, content, time=duration)

    def get_response_from_cache(self, env):
        cache_name = self.get_cache_name(env)
        if cache_name is None:
            return None
        body = self._storage.get(cache_name)
        logger.info('Getting from cache. Got %s',
                    (body if body is None else type(body)))
        if body is None:
            return None
        logger.info('Got from cache by `%s`', cache_name)
        return web.Response(body, content_type=self._content_type)

    def call_view(self, env, data):
        logger.info("Call view %s", env.request.url)
        response = self.next_handler(env, data)
        if response is not None:
            self.save_response_to_cache(env, response, self.get_duration(response))
            return response
        return None

    def __call__(self, env, data):
        if env.request.method not in ('GET', 'HEAD'):
            response = self.next_handler(env, data)
            logger.info("Cache skipped")
            return response
        
        cached = self.get_response_from_cache(env)
        if not cached:
            cached = self.call_view(env, data)
        return cached


    def cache(self, duration=None, content_type=None):
        if duration is None:
            duration = self._default_duration
        if content_type is None:
            content_type = self._content_type
        return CacheHandler(duration, content_type)

    def nocache(self):
        return NocacheHandler()


class CacheManagerWithContentType(CacheManager):
    _cache_name_length = 247

    def __init__(self, storage, default_duration, durations, content_type='text/html', content_type_prefix='ct:'):
        super(CacheManagerWithContentType, self).__init__(storage, default_duration, durations, content_type)
        self._ct_prefix = 'ct:'

    def save_response_to_cache(self, env, response, duration):
        super(CacheManagerWithContentType, self)\
            .save_response_to_cache(env, response, duration)
        
        content_type = response.headers.getall('content-type')
        if not content_type:
            content_type = self._content_type
        else:
            # XXX should we check if there is only one value as it done in WebOb?
            content_type = content_type[0]
        logger.info('Caching Content-Type `%s` for %i seconds %s', content_type,
                    duration, cache_name)
        self._storage.set(self._ct_prefix + cache_name, content_type, duration)


    def get_response_from_cache(self, env):
        response = super(CacheManagerWithContentType, self)\
            .get_response_from_cache(env)
        if response is None:
            return None
        content_type = self._storage.get(self._ct_prefix + cache_name)
        logger.info('Got from cache: %s , Content-Type: %s',
                    (body if body is None else type(body)), content_type)
        if content_type is None:
            return None
        response.content_type = content_type
        return response

