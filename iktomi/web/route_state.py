# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)


class RouteState(object):
    def __init__(self, request):
        self._prefixes = []
        # matched subdomain with aliases replaced by their main value
        self.primary_subdomains = []
        self.primary_domain = ''
        # remaining subdomain part for match
        self._domain = request.host.split(':', 1)[0].decode('idna')
        self.subdomain = self._domain
        self.request = request

    def add_prefix(self, prefix):
        self._prefixes.append(prefix)

    def pop_prefix(self):
        self._prefixes.pop()

    def add_subdomain(self, subdomain, alias_matched):
        if subdomain:
            self.primary_subdomains.insert(0, subdomain)
            self.primary_domain = '.'.join(self.primary_subdomains)
        if alias_matched:
            self.subdomain = self.subdomain[:-len(alias_matched)].rstrip('.')

    @property
    def path(self):
        path = self.request.path
        if self._prefixes:
            length = sum(map(len, self._prefixes))
            path = path[length:]
        return path

