# -*- coding: utf-8 -*-

__all__ = ['prefix', 'conf']

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
