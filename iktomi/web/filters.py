# -*- coding: utf-8 -*-

__all__ = ['match', 'method', 'static_files', 'ctype', 'prefix', 
           'subdomain', 'namespace']

import logging
import mimetypes
from os import path
from urllib import unquote
from .core import WebHandler
from .http import Response
from .url_templates import UrlTemplate
from .reverse import Location


logger = logging.getLogger(__name__)


def update_data(data, new_data):
    for k,v in new_data.items():
        setattr(data, k, v)


class match(WebHandler):

    def __init__(self, url='', name='', convs=None):
        self.url = url
        self.url_name = name
        self.builder = UrlTemplate(url, converters=convs)

    def match(self, env, data):
        matched, kwargs = self.builder.match(env._route_state.path, env=env)
        if matched:
            env.current_url_name = self.url_name
            update_data(data, kwargs)
            return self.next_handler(env, data)
        return None
    __call__ = match # for beautiful tracebacks

    def _locations(self):
        return {self.url_name: (Location(self.builder), {})}

    def __repr__(self):
        return '%s(\'%s\', \'%s\')' % \
                (self.__class__.__name__, self.url, self.url_name)


class method(WebHandler):
    def __init__(self, *names):
        self._names = set([name.upper() for name in names])
        if 'GET' in self._names:
            self._names.add('HEAD')

    def method(self, env, data):
        if env.request.method in self._names:
            return self.next_handler(env, data)
        return None
    __call__ = method

    def __repr__(self):
        return 'method(*%r)' % list(self._names)


class ctype(WebHandler):

    xml = 'application/xml'
    json = 'application/json'
    html = 'text/html'
    xhtml = 'application/xhtml+xml'

    def __init__(self, *types):
        self._types = types

    def ctype(self, env, data):
        if env.request.content_type in self._types:
            return self.next_handler(env, data)
        return None
    __call__ = ctype

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

    def static_files(self, env, data):
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
    __call__ = static_files


class prefix(WebHandler):
    def __init__(self, _prefix, convs=None):
        self.builder = UrlTemplate(_prefix, match_whole_str=False, 
                                   converters=convs)

    def prefix(self, env, data):
        matched, kwargs = self.builder.match(env._route_state.path, env=env)
        if matched:
            update_data(data, kwargs)
            env._route_state.add_prefix(self.builder(**kwargs))
            result = self.next_handler(env, data)
            if result is not None:
                return result
            env._route_state.pop_prefix()
        return None
    __call__ = prefix

    def _locations(self):
        locations = super(prefix, self)._locations()
        for location, scope in locations.values():
            location.builders.insert(0, self.builder)
        return locations

    def __repr__(self):
        return '%s(\'%r\')' % (self.__class__.__name__, self.builder)


class subdomain(WebHandler):
    def __init__(self, _subdomain):
        self.subdomain = unicode(_subdomain)

    def subdomain(self, env, data):
        subdomain = env._route_state.subdomain
        #XXX: here we can get 'idna' encoded sequence, that is the bug
        if self.subdomain:
            slen = len(self.subdomain)
            delimiter = subdomain[-slen-1:-slen]
            matches = subdomain.endswith(self.subdomain) and delimiter in ('', '.')
        else:
            matches = not subdomain
        if matches:
            env._route_state.add_subdomain(self.subdomain)
            return self.next_handler(env, data)
        return None
    __call__ = subdomain

    def _locations(self):
        locations = super(subdomain, self)._locations()
        for location, scope in locations.values():
            location.subdomains.append(self.subdomain)
        return locations

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.subdomain)


class namespace(WebHandler):
    def __init__(self, ns):
        # namespace is str
        self.namespace = ns

    def namespace(self, env, data):
        if hasattr(env, 'namespace'):
            env.namespace += '.' + self.namespace
        else:
            env.namespace = self.namespace
        return self.next_handler(env, data)
    __call__ = namespace

    def _locations(self):
        namespaces = self.namespace.split('.')
        locations = super(namespace, self)._locations()
        for ns in namespaces[::-1]:
            locations = {ns: (Location(), locations)}
        return locations


