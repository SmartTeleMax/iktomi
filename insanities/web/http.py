# -*- coding: utf-8 -*-

__all__ = ['Request', 'Response']

import logging
import httplib
import cgi
from webob import Request as _Request, Response
from webob.multidict import MultiDict, NoVars, UnicodeMultiDict

from ..utils import cached_property

logger = logging.getLogger(__name__)


class PathPrefixes(object):
    def __init__(self, request):
        self._prefixes = []
        self._subdomain = ''
        self._domain = request.server_name.decode('idna')
        self.request = request

    def add_prefix(self, prefix):
        self._prefixes.append(prefix)

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


class Request(_Request):
    '''
    Patched webob Request class
    '''

    @cached_property
    def FILES(self):
        return self._sub_post(lambda x: isinstance(x[1], cgi.FieldStorage))

    @cached_property
    def POST(self):
        return self._sub_post(lambda x: not isinstance(x[1], cgi.FieldStorage))

    def _sub_post(self, condition):
        post = super(Request, self).str_POST
        if isinstance(post, NoVars):
            return post
        return UnicodeMultiDict(MultiDict(filter(condition, post.items())),
                                encoding=self.charset,
                                errors=self.unicode_errors,
                                decode_keys=self.decode_param_names)
