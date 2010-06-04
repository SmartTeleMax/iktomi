# -*- coding: utf-8 -*-

__all__ = ['prefix', 'subdomain', 'Conf']

import logging
import re
import httplib
from os import path
from .core import Wrapper, STOP
from ..utils.url import UrlTemplate
from .filters import match


logger = logging.getLogger(__name__)


class prefix(Wrapper):

    def __init__(self, _prefix):
        super(prefix, self).__init__()
        self.builder = UrlTemplate(_prefix, match_whole_str=False)

    def trace(self, tracer):
        tracer.builder(self.builder)

    def handle(self, rctx):
        matched, kwargs = self.builder.match(rctx.request.path)
        if matched:
            rctx.data.update(kwargs)
            rctx.request.add_prefix(self.builder(**kwargs))
            rctx = self.exec_wrapped(rctx)
            return rctx
        return STOP

    def __repr__(self):
        return u'%s(\'%r\')' % (self.__class__.__name__, self.builder)


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
        return STOP

    def __repr__(self):
        return u'%s(\'%s\')' % (self.__class__.__name__, self.subdomain)


class Conf(Wrapper):

    def __init__(self, ns, **kwargs):
        super(Conf, self).__init__()
        # namespace is str, may be empty for default namespace
        self.namespace = ns
        self.conf = kwargs

    def handle(self, rctx):
        if self.namespace:
            rctx.conf.push(self.namespace)
        rctx.conf.update(self.conf)
        rctx = self.exec_wrapped(rctx)
        if self.namespace:
            rctx.conf.pop()
        return rctx

    def trace(self, tracer):
        if self.namespace:
            tracer.namespace(self.namespace)
