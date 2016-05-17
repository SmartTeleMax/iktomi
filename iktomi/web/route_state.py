# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)


class RouteState(object):
    def __init__(self, request):
        self._prefixes = ()
        # matched subdomain with aliases replaced by their main value
        self.primary_subdomains = () # tuple to be sure it's readonly
        self.primary_domain = ''
        # remaining subdomain part for match
        self._domain = request.host.split(':', 1)[0].encode('utf-8').decode('idna')
        self.subdomain = self._domain
        self.request = request

    def __copy__(self):
        copy = object.__new__(type(self))
        copy.__dict__.update(self.__dict__)
        return copy

    def add_prefix(self, prefix):
        self = self.__copy__()
        self._prefixes += (prefix,)
        return self

    def add_subdomain(self, subdomain, alias_matched):
        self = self.__copy__()
        if subdomain:
            self.primary_subdomains = (subdomain, ) + self.primary_subdomains
            self.primary_domain = '.'.join(self.primary_subdomains)
        if alias_matched:
            self.subdomain = self.subdomain[:-len(alias_matched)].rstrip('.')
        return self

    @property
    def path(self):
        path = self.request.path
        if self._prefixes:
            length = sum(map(len, self._prefixes))
            path = path[length:]
        return path

