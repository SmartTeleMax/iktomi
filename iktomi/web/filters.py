# -*- coding: utf-8 -*-

__all__ = ['match', 'method', 'static_files', 'prefix', 
           'subdomain', 'namespace', 'by_method']

import six
import logging
import os
from os import path
from six.moves.urllib.parse import unquote
from webob.exc import HTTPMethodNotAllowed, HTTPNotFound
from webob.static import FileApp
from .core import WebHandler, cases
from . import Response
from .url_templates import UrlTemplate
from .reverse import Location
from iktomi.utils.deprecation import deprecated


logger = logging.getLogger(__name__)


def update_data(data, new_data):
    for k,v in new_data.items():
        setattr(data, k, v)


class match(WebHandler):
    '''
    Checks if current request path completely matches given `url` pattern.
    If there are any `web.prefix` handlers in the chain before current,
    all matched prefixes are taken into account.

    Adds an endpoint to reverse url map with given `name` under the
    current namespace.
    If the name is empty, url name is equal to current namespace name::

        web.match('/', 'index') | index,
        web.match('/by-date/<date:dt>', 'by_date',
                  convs={'date': MyDateUrlConv}) | by_date,
    '''


    def __init__(self, url='', name='', fragment=None, convs=None):
        self.url = url
        self.url_name = name
        self.fragment = fragment
        self.builder = UrlTemplate(url, converters=convs)

        self.fragment = fragment
        if self.fragment is not None:
            self.fragment_builder = UrlTemplate(self.fragment, converters=convs)
        else:
            self.fragment_builder = None

    def match(self, env, data):
        matched, kwargs = self.builder.match(env._route_state.path, env=env)
        if matched is not None:
            env.current_url_name = self.url_name
            update_data(data, kwargs)
            return self.next_handler(env, data)
        return None
    __call__ = match # for beautiful tracebacks

    def _locations(self):
        location = Location(self.builder,
                            fragment_builder=self.fragment_builder)
        return {self.url_name: (location, {})}

    def __repr__(self):
        return '{}({!r}, {!r})'.format(self.__class__.__name__,
                                       self.url, self.url_name)


class prefix(WebHandler):
    '''
    Checks if current request path matches given `url` pattern.
    It can remain an unmatched url part after mathced one.
    If there are any `web.prefix` handlers in the chain before current,
    all matched prefixes are taken into account.

    If name argument is provided, it is equal to::

        web.prefix(...) | web.namespace(name)

    Sample usage::

        web.prefix('/news', name='news') | web.cases(
            web.match() | index,
            web.match('/page/<int:page>', 'page') | page
            ),
    '''

    def __init__(self, _prefix, convs=None, name=None):
        self.url = _prefix
        self.builder = UrlTemplate(_prefix, match_whole_str=False, 
                                   converters=convs)
        if name is not None:
            # A shortcut for prefix(..) | namespace(name)
            self._next_handler = namespace(name)

    def prefix(self, env, data):
        matched, kwargs = self.builder.match(env._route_state.path, env=env)
        if matched is not None:
            update_data(data, kwargs)
            env._route_state = env._route_state.add_prefix(matched)
            result = self.next_handler(env, data)
            if result is not None:
                return result
        return None
    __call__ = prefix

    def _locations(self):
        locations = WebHandler._locations(self)
        for location, scope in locations.values():
            location.builders.insert(0, self.builder)
        return locations

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.url)


class namespace(WebHandler):
    '''
    Wraps all next handlers into url namespace with given name.
    '''

    def __init__(self, ns):
        if not ns:
            raise TypeError('Namespace must not be empty')
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
        locations = WebHandler._locations(self)
        all_locations = [x[0] for x in locations.values()]

        # extract all common builders and subdomains from nested locations
        # and put them into namespace's location.
        # This allows to write prefixes and subdomains after namespaces:
        # prefix() | namespace() | prefix() | match()
        builders = []
        while all_locations and all_locations[0].builders:
            builder = all_locations[0].builders[0]
            if len(all_locations) > 1 and \
                not any(not (x.builders and x.builders[0] is builder)
                        for x in all_locations[1:]):
                builders.append(builder)
                for loc in all_locations:
                    loc.builders.pop(0)
            else:
                break

        # XXX do we need to do the same with subdomains?
        #     It makes everything more clear, but does not make an effect,
        #     because we have no pattern matching here
        subdomains = []
        while all_locations and all_locations[0].subdomains:
            subdomain = all_locations[0].subdomains[-1]
            if any(x.subdomains and x.subdomains[-1] is subdomain
                   for x in all_locations[1:]):
                subdomains.insert(0, subdomain)
                for loc in all_locations:
                    loc.subdomains.pop()
            else:
                break

        namespaces = self.namespace.split('.')
        for ns in namespaces[::-1]:
            locations = {ns: (Location(), locations)}

        for loc in locations.values():
            loc[0].builders = builders
            loc[0].subdomains = subdomains

        return locations


class method(WebHandler):

    '''Checks whether request method is in a list of allowed methods.

    If `strict=True`, raises `webob.exc.HTTPMethodNotAllowed` on wrong method,
    otherwise returns `None` ("continue route" signal)::

        web.method('GET', 'POST', strict=True) | handler
    '''

    def __init__(self, *names, **kw):
        self._names = set([name.upper() for name in names])
        if 'GET' in self._names:
            self._names.add('HEAD')
        self.strict = kw.pop('strict', False)
        assert not kw

    def method(self, env, data):
        if env.request.method in self._names:
            return self.next_handler(env, data)
        if self.strict:
            raise HTTPMethodNotAllowed()
        return None
    __call__ = method

    def __repr__(self):
        return 'method({})'.format(', '.join(repr(n) for n in self._names))


class by_method(cases):
    '''
    Cases chooser handler::

        by_method({'GET': get_item_handler,
                   'POST': save_item_handler})
    '''

    def __init__(self, handlers_dict, default_handler=None):
        handlers = []
        for methods, handler in handlers_dict.items():
            if isinstance(methods, six.string_types):
                methods = (methods,)
            handlers.append(method(*methods, strict=False) | handler)
        if default_handler is not None:
            handlers.append(default_handler)
        else:
            handlers.append(HTTPMethodNotAllowed())
        cases.__init__(self, *handlers)


class subdomain(WebHandler):
    '''
    Checks if current request domain matches given one.

    `subdomains`: a list of following values in order they are
    attempted to match:

        * string — domain part (without dots after and before)
        * empty string — no pattern is matched and there must not
          remain any unmatched domain part, subdomain matching is finished
        * `None` — no pattern is matched and but there can remain
          an unmatched domain part, subdomain matching can
          continue in next handlers

    `name`: shortcut for namespace handler chained next to subdomain:
        ::

            web.subdomain(...) | web.namespace(name)

    `primary`: one of subdomains, used to reverse an url with this 
    subdomain from other domains. 
    All other subdomains are aliases to primary subdomain.
    By default, the first subdomain.
    '''

    def __init__(self, *subdomains, **kwargs):
        self.subdomains = subdomains

        # this attribute is used for ducktyping in Location, be careful
        self.primary = kwargs.pop('primary', self.subdomains[0])
        assert self.primary in self.subdomains

        name = kwargs.pop('name', None)
        if name is not None:
            # A shortcut for subdomain(..) | namespace(name)
            self._next_handler = namespace(name)

        if kwargs: # pragma: no cover
            raise TypeError("subdomain.__init__ got an unexpected keyword "
                            "arguments {}".format(",".join(kwargs)))

    def subdomain(self, env, data):
        subdomain = env._route_state.subdomain
        #XXX: here we can get 'idna' encoded sequence, that is the bug
        for subd in self.subdomains:
            if subd:
                slen = len(subd)
                delimiter = subdomain[-slen-1:-slen]
                matches = subdomain.endswith(subd) and delimiter in ('', '.')
            elif subd is None:
                # continue matching 
                matches = True
            elif subd == '':
                # no subdomains are allowed
                matches = not subdomain

            if matches:
                env._route_state = \
                        env._route_state.add_subdomain(self.primary, subd)
                return self.next_handler(env, data)
        return None
    __call__ = subdomain

    def _locations(self):
        locations = WebHandler._locations(self)
        for location, scope in locations.values():
            location.subdomains.append(self)
        return locations

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.subdomains)


class static_files(WebHandler):
    '''
    Static file handler for dev server (not recommended in production)::

       static_files('/path/to/static', url='/static/')
    '''

    def __init__(self, location, url='/static/'):
        self.location = location
        self.url = url

    def url_for_static(self, part):
        while part.startswith('/'):
            part = part[1:]
        return path.join(self.url, part)

    @deprecated("Use static.url_for_static instead")
    def construct_reverse(self): # pragma: no cover
        return self.url_for_static

    def translate_path(self, pth):
        """Translate a /-separated PATH to the local filename syntax."""
        # initially copied from SimpleHTTPServer
        words = pth.split('/')
        words = filter(None, words)
        pth = self.location
        for word in words:
            # Do not allow path separators other than /,
            # drive names and . ..
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if drive or head or word in (os.curdir, os.pardir):
                return None
            pth = os.path.join(pth, word)

        assert pth.startswith(self.location + '/')
        assert pth == path.normpath(pth)
        return pth

    def static_files(self, env, data):
        path_info = unquote(env.request.path)
        if path_info.startswith(self.url):
            if path_info.endswith('/'):
                raise HTTPNotFound
            file_path = self.translate_path(path_info[len(self.url):])
            if file_path and path.exists(file_path) and path.isfile(file_path):
                return FileApp(file_path)
            else:
                logger.info('Client requested non existent static data "%s"',
                            file_path)
                return Response(status=404)
        return None
    __call__ = static_files

    def __repr__(self):
        return '{}({!r}, {!r})'.format(self.__class__.__name__, 
                                       self.location, self.url)

