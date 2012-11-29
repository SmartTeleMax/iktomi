# -*- coding: utf-8 -*-

__all__ = ['Reverse', 'UrlBuildingError']

from .url import URL
from .url_templates import UrlBuildingError
from ..utils import cached_property
from collections import namedtuple


SubLocation = namedtuple('SubLocation', ['builders', 'subdomains'])

class Location(object):
    def __init__(self, *builders, **kwargs):
        self.locations = [SubLocation(list(builders),
                                      kwargs.get('subdomains', []))]

    @property
    def need_arguments(self):
        for l in self.locations:
            if not any(b._url_params for b in l[0]):
                return False
        return True

    def build_path(self, **kwargs):
        if not self.locations:
            return '', ''
        kw_set = set(kwargs)
        endpoint, diff = None, None
        for l in self.locations:
            b_set = set(sum([b._url_params.keys() for b in l.builders], []))
            if not b_set.difference(kw_set):
                ldiff = len(kw_set.difference(b_set))
                if endpoint is None or ldiff < diff:
                    endpoint, diff = l, ldiff

        if endpoint is None:
            raise UrlBuildingError(u'Not all URL build arguments are provided')
        return '.'.join(endpoint.subdomains), \
                ''.join([b(**kwargs) for b in endpoint.builders])

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.locations == other.locations

    def __repr__(self):
        return '%s(*%r)' % (self.__class__.__name__, self.locations)



class Reverse(object):
    def __init__(self, scope, location=None, path='', host='', ready=False, 
                 need_arguments=False, is_root=False, bound_request=None):
        # XXX document, what is scope and what is location!
        self._location = location
        self._scope = scope
        self._path = path
        self._host = host
        self._ready = ready
        self._need_arguments = need_arguments
        self._is_endpoint = (not self._scope) or ('' in self._scope)
        self._is_scope = bool(self._scope)
        self._is_root = is_root # XXX is_root
        self._bound_request = bound_request

    def __call__(self, **kwargs):
        if self._ready:
            raise UrlBuildingError('Endpoint do not accept arguments')
        if self._is_endpoint:
            path, host = self._path, self._host
            if self._location:
                h, p = self._location.build_path(**kwargs)
                host += h
                path += p
            if self._scope:
                location = self._scope[''][0]
                h, p = location.build_path(**kwargs)
                host += h
                path += p
            return self.__class__(self._scope, self._location, path=path, host=host,
                                  bound_request=self._bound_request, ready=True)
        raise UrlBuildingError('Not an endpoint')

    def bind_to_request(self, bound_request):
        return self.__class__(self._scope, self._location,
                              path=self._path, host=self._host,
                              ready=self._ready,
                              need_arguments=self._need_arguments,
                              is_root=self._is_root,
                              bound_request=bound_request)

    #@cached_property
    #def url_arguments(self):
    #    args = set()
    #    if self._is_endpoint:
    #        if self._location:
    #            args |= self._location.url_arguments
    #        if self._scope:
    #            args |= self._scope[''][0].url_arguments
    #    return args

    def __getattr__(self, name):
        if self._is_scope and name in self._scope:
            if self._need_arguments:
                raise UrlBuildingError('Need arguments to build last part of url')
            location, scope = self._scope[name]
            path = self._path
            host = self._host
            ready = not location.need_arguments
            if ready:
                h, p = location.build_path()
                host += h
                path += p
            return self.__class__(scope, location, path, host, ready,
                                  bound_request=self._bound_request,
                                  need_arguments=location.need_arguments)
        raise UrlBuildingError('Namespace or endpoint %s does not exist'
                               % name)

    def build_url(self, _name, **kwargs):
        subreverse = self
        #used_args = set()
        for part in _name.split('.'):
            if not subreverse._ready and subreverse._is_endpoint:
                #used_args |= subreverse.url_arguments
                subreverse = subreverse(**kwargs)
            subreverse = getattr(subreverse, part)
        if not subreverse._ready and subreverse._is_endpoint:
            #used_args |= subreverse.url_arguments
            subreverse = subreverse(**kwargs)

        #if set(kwargs).difference(used_args):
        #    raise UrlBuildingError('Not all arguments are used during URL building: %s' %
        #                           ', '.join(set(kwargs).difference(used_args)))
        return subreverse.as_url

    @property
    def as_url(self):
        if not self._is_endpoint:
            raise UrlBuildingError('Not an endpoint')

        if self._ready:
            path, host = self._path, self._host
        elif self._is_root:
            location, scope = self._scope['']
            if not location.need_arguments:
                host, path = location.build_path()
            else:
                raise UrlBuildingError('Need arguments to be build')
        else:
            raise UrlBuildingError('Not an endpoint')

        # XXX there is a little mess with `domain` and `host` terms
        if ':' in host:
            domain, port = host.split(':')
        else:
            domain = host
            port = None

        if self._bound_request:
            bound_domain, bound_port = self._bound_request.host.split(':')
            scheme_port = {'http': '80',
                           'https': '443'}.get(self._bound_request.scheme, '80')
            port = port or bound_port

            return URL(path, host=domain or bound_domain,
                       port=port if port != scheme_port else None,
                       schema=self._bound_request.scheme,
                       show_host=host and (domain != bound_domain \
                                           or port != bound_port))
        return URL(path, host=domain, port=port, show_host=True)

    @classmethod
    def from_handler(cls, handler, env=None):
        from .core import locations
        return cls(locations(handler), is_root=True)
