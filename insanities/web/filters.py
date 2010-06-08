# -*- coding: utf-8 -*-

__all__ = ['match', 'method', 'static', 'ctype']

import logging
import re
import httplib
from os import path
from .core import RequestHandler, STOP
from .http import HttpException
from ..utils.url import UrlTemplate


logger = logging.getLogger(__name__)


class match(RequestHandler):

    def __init__(self, url, name, converters=None):
        super(match,self).__init__()
        self.url = url
        self.url_name = name
        self.builder = UrlTemplate(url)

    def trace(self, tracer):
        tracer.url_name(self.url_name)
        tracer.builder(self.builder)

    def handle(self, rctx):
        matched, kwargs = self.builder.match(rctx.request.path)
        if matched:
            rctx.data.update(kwargs)
            return rctx.next()
        return STOP

    def __repr__(self):
        return '%s(\'%s\', \'%s\')' % \
                (self.__class__.__name__, self.url, self.url_name)


class method(RequestHandler):

    def __init__(self, *names):
        super(method, self).__init__()
        self._names = [name.upper() for name in names]

    def handle(self, rctx):
        if rctx.request.method in self._names:
            return rctx.next()
        return STOP

    def __repr__(self):
        return 'method(*%r)' % self._names


class ctype(RequestHandler):

    xml = 'application/xml'
    json = 'application/json'
    html = 'text/html'
    xhtml = 'application/xhtml+xml'

    def __init__(self, *types):
        super(ctype, self).__init__()
        self._types = types

    def handle(self, rctx):
        if rctx.request.content_type in self._types:
            return rctx.next()
        return STOP

    def __repr__(self):
        return '%s(*%r)' % (self.__class__.__name__, self._types)


def static(rctx):
    def url_for_static(part):
        return path.join(rctx.conf.STATIC_URL, part)

    rctx.data['url_for_static'] = url_for_static

    if rctx.request.path.startswith(rctx.conf.STATIC_URL):
        static_path = rctx.request.path[len(rctx.conf.STATIC_URL):]
        file_path = path.join(rctx.conf.STATIC, static_path)
        if path.exists(file_path) and path.isfile(file_path):
            with open(file_path, 'r') as f:
                rctx.response.write(f.read())
            return rctx.next()
        else:
            raise HttpException(httplib.NOT_FOUND)
    return STOP
