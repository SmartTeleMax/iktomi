# -*- coding: utf-8 -*-

__all__ = ['prefix', 'subdomain', 'namespace', 'Conf']

import logging
import re
import httplib
from urllib import quote
from os import path
from .core import RequestHandler, STOP
from ..utils.url import UrlTemplate
from .filters import match


logger = logging.getLogger(__name__)


class prefix(RequestHandler):

    def __init__(self, _prefix):
        self.builder = UrlTemplate(_prefix, match_whole_str=False)

    def trace(self, tracer):
        tracer.builder(self.builder)

    def handle(self, rctx):
        matched, kwargs = self.builder.match(rctx.request.path, rctx=rctx)
        if matched:
            rctx.data.update(kwargs)
            rctx.request.add_prefix(quote(self.builder(**kwargs).encode('utf-8')))
            return rctx.next()
        return STOP

    def __repr__(self):
        return '%s(\'%r\')' % (self.__class__.__name__, self.builder)


class subdomain(RequestHandler):

    def __init__(self, _subdomain):
        self.subdomain = unicode(_subdomain)

    def trace(self, tracer):
        if self.subdomain:
            tracer.subdomain(self.subdomain)

    def handle(self, rctx):
        subdomain = rctx.request.subdomain
        #XXX: here we can get 'idna' encoded sequence, that is the bug
        if self.subdomain:
            slen = len(self.subdomain)
            delimiter = subdomain[-slen-1:-slen]
            matches = subdomain.endswith(self.subdomain) and delimiter in ('', '.')
        else:
            matches = not subdomain

        if matches:
            #XXX: here we add subdomain prefix. What codec we need 'utf-8' or 'idna'
            rctx.request.add_subdomain(quote(self.subdomain.encode('utf-8')))
            #rctx.request.add_subdomain(self.subdomain)
            return rctx.next()
        return STOP

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.subdomain)


class namespace(RequestHandler):
    def __init__(self, ns):
        # namespace is str
        self.namespace = ns

    def handle(self, rctx):
        if rctx.conf['namespace']:
            rctx.conf['namespace'] += '.' + self.namespace
        else:
            rctx.conf['namespace'] = self.namespace
        return rctx.next()

    def trace(self, tracer):
        tracer.namespace(self.namespace)


class Conf(RequestHandler):

    def __init__(self, **kwargs):
        self.conf = kwargs

    def handle(self, rctx):
        rctx.conf.update(self.conf)
        return rctx.next()
