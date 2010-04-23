# -*- coding: utf-8 -*-

__all__ = ['prefix', 'subdomain', 'Conf']

import logging
import re
import httplib
from os import path
from .core import Wrapper, ContinueRoute
from .http import RequestContext, HttpException


logger = logging.getLogger(__name__)


class prefix(Wrapper):

    def __init__(self, _prefix):
        super(prefix, self).__init__()
        self.prefix = _prefix

    def trace(self, tracer):
        tracer.prefix(self.prefix)

    def handle(self, rctx):
        if rctx.request.path.startswith(self.prefix):
            rctx.request.add_prefix(self.prefix)
            rctx = self.exec_wrapped(rctx)
            return rctx
        raise ContinueRoute(self)

    def __repr__(self):
        return '%s(\'%s\')' % (self.__class__.__name__, self.prefix)

class subdomain(Wrapper):

    def __init__(self, _subdomain):
        super(subdomain, self).__init__()
        self.subdomain = _subdomain

    def trace(self, tracer):
        if self.subdomain:
            tracer.subdomain(self.subdomain)

    def handle(self, rctx):
        subdomain = rctx.request.subdomain
        if self.subdomain:
            slen = len(self.subdomain)
            delimiter = subdomain[-slen-1:-slen]
            matches = subdomain.endswith(self.subdomain) and delimiter in ('', '.')
        else:
            matches = not subdomain
        
        if matches:
            rctx.request.add_subdomain(self.subdomain)
            rctx = self.exec_wrapped(rctx)
            return rctx
        raise ContinueRoute(self)

    def __repr__(self):
        return '%s(\'%s\')' % (self.__class__.__name__, self.subdomain)


class Conf(Wrapper):

    handlers = []

    def __init__(self, ns, **kwargs):
        super(Conf, self).__init__()
        # namespace is str, may be empty for default namespace
        self.namespace = ns
        self.conf = kwargs

    def handle(self, rctx):
        if self.namespace:
            rctx.conf.push(self.namespace)
        for conf_handler in self.handlers:
            conf_handler(rctx, self.conf)
        rctx = self.exec_wrapped(rctx)
        if self.namespace:
            rctx.conf.pop()
        return rctx

    def trace(self, tracer):
        if self.namespace:
            tracer.namespace(self.namespace)
