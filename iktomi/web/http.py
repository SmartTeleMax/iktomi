# -*- coding: utf-8 -*-

__all__ = ['Request', 'Response']

import logging
from webob import Request, Response

logger = logging.getLogger(__name__)


class RouteState(object):
    def __init__(self, request):
        self._prefixes = []
        self._subdomain = ''
        self._domain = request.host.split(':', 1)[0].decode('idna')
        self.request = request

    def add_prefix(self, prefix):
        self._prefixes.append(prefix)

    def pop_prefix(self):
        self._prefixes.pop()

    def add_subdomain(self, subdomain):
        if self._subdomain and subdomain:
            self._subdomain = subdomain + '.' + self._subdomain
        elif subdomain:
            self._subdomain = subdomain

    @property
    def path(self):
        path = self.request.path
        if self._prefixes:
            length = sum(map(len, self._prefixes))
            path = path[length:]
        return path

    @property
    def path_qs(self):
        path = self.request.path_qs
        if self._prefixes:
            length = sum(map(len, self._prefixes))
            path = path[length:]
        return path

    @property
    def subdomain(self):
        if self._subdomain:
            return self._domain[:-len(self._subdomain)-1]
        return self._domain


