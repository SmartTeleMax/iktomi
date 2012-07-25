# -*- coding: utf-8 -*-

__all__ = ['Reverse', 'UrlBuildingError']

from .url import URL
from .url_templates import UrlBuildingError
from ..utils import cached_property



class Location(object):
    def __init__(self, *builders, **kwargs):
        self.builders = list(builders)
        self.subdomains = kwargs.get('subdomains', [])

    @property
    def need_arguments(self):
        for b in self.builders:
            if b._url_params:
                return True
        return False

    def build_path(self, **kwargs):
        result = []
        for b in self.builders:
            result.append(b(**kwargs))
        return ''.join(result)

    def build_subdomians(self):
        return u'.'.join(self.subdomains)

    @property
    def url_arguments(self):
        return reduce(lambda x,y: x|set(y._url_params), self.builders, set())

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.builders == other.builders and self.subdomains == other.subdomains

    def __repr__(self):
        return '%s(*%r, %r)' % (self.__class__.__name__, self.builders, self.subdomains)



class Reverse(object):
    def __init__(self, scope, location=None, path='', host='', ready=False, 
                 need_arguments=False, root=False, bound_request=None):
        # XXX document, what is scope and what is location!
        self._location = location
        self._scope = scope
        self._path = path
        self._host = host
        self._ready = ready
        self._need_arguments = need_arguments
        self._is_endpoint = (not self._scope) or ('' in self._scope)
        self._is_scope = bool(self._scope)
        self._root = root
        self._bound_request = bound_request

    def __call__(self, **kwargs):
        if self._ready:
            raise UrlBuildingError('Endpoint do not accept arguments')
        if self._is_endpoint:
            path, host = self._path, self._host
            if self._location:
                host += self._location.build_subdomians()
                path += self._location.build_path(**kwargs)
            if self._scope:
                location = self._scope[''][0]
                host += location.build_subdomians()
                path += location.build_path(**kwargs)
            return self.__class__(self._scope, self._location, path=path, host=host,
                                  bound_request=self._bound_request, ready=True)
        raise UrlBuildingError('Not an endpoint')

    def bind_to_request(self, bound_request):
        return self.__class__(self._scope, self._location,
                              path=self._path, host=self._host,
                              ready=self._ready,
                              need_arguments=self._need_arguments,
                              root=self._root,
                              bound_request=bound_request)

    @cached_property
    def url_arguments(self):
        args = set()
        if self._is_endpoint:
            if self._location:
                args |= self._location.url_arguments
            if self._scope:
                args |= self._scope[''][0].url_arguments
        return args

    def __getattr__(self, name):
        if self._is_scope and name in self._scope:
            if self._need_arguments:
                raise UrlBuildingError('Need arguments to build last part of url')
            location, scope = self._scope[name]
            path = self._path
            host = self._host
            ready = not location.need_arguments
            if ready:
                path += location.build_path()
                host += location.build_subdomians()
            return self.__class__(scope, location, path, host, ready,
                                  bound_request=self._bound_request,
                                  need_arguments=location.need_arguments)
        raise AttributeError(name)

    def build_url(self, _name, **kwargs):
        subreverse = self
        used_args = set()
        for part in _name.split('.'):
            if not subreverse._ready and subreverse._is_endpoint:
                used_args |= subreverse.url_arguments
                subreverse = subreverse(**kwargs)
            subreverse = getattr(subreverse, part)
        if not subreverse._ready and subreverse._is_endpoint:
            used_args |= subreverse.url_arguments
            subreverse = subreverse(**kwargs)

        if set(kwargs).difference(used_args):
            raise UrlBuildingError('Not all arguments are used during URL building: %s' %
                                   ', '.join(set(kwargs).difference(used_args)))
        return subreverse.as_url

    @property
    def as_url(self):
        if self._ready:
            path, host = self._path, self._host
        elif self._is_endpoint and self._root:
            location, scope = self._scope['']
            if not location.need_arguments:
                path = location.build_path()
                host = location.build_subdomians()
            else:
                raise UrlBuildingError('Need arguments to be build')
        else:
            raise UrlBuildingError('Not an endpoint')

        if self._bound_request:
            return URL(path, host=host,
                       port=self._bound_request.port,
                       schema=self.bound_request.schema,
                       show_host=host and host != self._bound_request.host)
        return URL(path, host=host, show_host=True)

    @classmethod
    def from_handler(cls, handler, env=None):
        from .core import locations
        return cls(locations(handler), root=True)
