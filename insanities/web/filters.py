# -*- coding: utf-8 -*-

__all__ = ['match', 'method', 'static_files', 'ctype', 'prefix', 
           'subdomain', 'namespace']

import logging
import httplib
import mimetypes
from os import path
from urllib import unquote
from .core import WebHandler
from .http import Response
from .url import UrlTemplate


logger = logging.getLogger(__name__)


def update_data(data, new_data):
    for k,v in new_data.items():
        data[k] = v


class match(WebHandler):

    def __init__(self, url, name, convs=None):
        self.url = url
        self.url_name = name
        self.builder = UrlTemplate(url, converters=convs)

    def _locations(self):
        return {self.url_name: {'builders': [self.builder]}}

    def handle(self, env, data, next_handler):
        matched, kwargs = self.builder.match(env.request.prefixed_path, env=env)
        if matched:
            env.current_url_name = self.url_name
            update_data(data, kwargs)
            return next_handler(env, data)
        return None

    def __repr__(self):
        return '%s(\'%s\', \'%s\')' % \
                (self.__class__.__name__, self.url, self.url_name)


class method(WebHandler):
    def __init__(self, *names):
        self._names = [name.upper() for name in names]

    def handle(self, env, data, next_handler):
        if env.request.method in self._names:
            return next_handler(env, data)
        return None

    def __repr__(self):
        return 'method(*%r)' % self._names


class ctype(WebHandler):

    xml = 'application/xml'
    json = 'application/json'
    html = 'text/html'
    xhtml = 'application/xhtml+xml'

    def __init__(self, *types):
        self._types = types

    def handle(self, env, data, next_handler):
        if env.request.content_type in self._types:
            return next_handler(env, data)
        return None

    def __repr__(self):
        return '%s(*%r)' % (self.__class__.__name__, self._types)


class static_files(WebHandler):
    def __init__(self, location, url='/static/'):
        self.location = location
        self.url = url

    def construct_reverse(self):
        def url_for_static(part):
            while part.startswith('/'):
                part = part[1:]
            return path.join(self.url, part)
        return url_for_static

    def handle(self, env, data, next_handler):
        path_info = unquote(env.request.path)
        if path_info.startswith(self.url):
            static_path = path_info[len(self.url):]
            while static_path[0] in ('.', '/', '~'):
                static_path = static_path[1:]
            file_path = path.join(self.location, static_path)
            if path.exists(file_path) and path.isfile(file_path):
                mime = mimetypes.guess_type(file_path)[0]
                response = Response()
                if mime:
                    response.content_type = mime
                with open(file_path, 'r') as f:
                    response.write(f.read())
                return response
            else:
                logger.info('Client requested non existent static data "%s"' % file_path)
                return Response(status=404)
        return None


class prefix(WebHandler):
    def __init__(self, _prefix, convs=None):
        self.builder = UrlTemplate(_prefix, match_whole_str=False, 
                                   converters=convs)

    def _locations(self):
        locations = super(prefix, self)._locations()
        for v in locations.values():
            v.setdefault('builders', []).append(self.builder)
        return locations

    def handle(self, env, data, next_handler):
        matched, kwargs = self.builder.match(env.request.prefixed_path, env=env)
        if matched:
            update_data(data, kwargs)
            env.request.add_prefix(self.builder(**kwargs))
            return next_handler(env, data)
        return None

    def __repr__(self):
        return '%s(\'%r\')' % (self.__class__.__name__, self.builder)


class subdomain(WebHandler):
    def __init__(self, _subdomain):
        self.subdomain = unicode(_subdomain)

    def _locations(self):
        locations = super(subdomain, self)._locations()
        for v in locations.values():
            v.setdefault('subdomains', []).append(self.subdomain)
        return locations

    def handle(self, env, data, next_handler):
        subdomain = env.request.subdomain
        #XXX: here we can get 'idna' encoded sequence, that is the bug
        if self.subdomain:
            slen = len(self.subdomain)
            delimiter = subdomain[-slen-1:-slen]
            matches = subdomain.endswith(self.subdomain) and delimiter in ('', '.')
        else:
            matches = not subdomain

        if matches:
            env.request.add_subdomain(self.subdomain)
            return next_handler(env, data)
        return None

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.subdomain)


class namespace(WebHandler):
    def __init__(self, ns):
        # namespace is str
        self.namespace = ns

    def handle(self, env, data, next_handler):
        if 'namespace' in env:
            env.namespace += '.' + self.namespace
        else:
            env.namespace = self.namespace
        return next_handler(env, data)

    def _locations(self):
        locations = super(namespace, self)._locations()
        new_locations = {}
        for k, v in locations.items():
            new_locations[self.namespace+'.'+k if k else self.namespace] = v
        return new_locations
