# -*- coding: utf-8 -*-

__all__ = ['match', 'method', 'static_files', 'ctype']

import logging
import re
import httplib
import mimetypes
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
        matched, kwargs = self.builder.match(rctx.request.path, rctx=rctx)
        if matched:
            rctx.conf.url_name = self.url_name
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


class static_files(RequestHandler):

    def __init__(self, location, url='/static/'):
        self.location = location
        self.url = url

    def add_reverse(self, rctx):
        def url_for_static(part):
            while part.startswith('/'):
                part = part[1:]
            return path.join(self.url, part)
        rctx.vals['url_for_static'] = url_for_static
        return rctx.next()

    def handle(self, rctx):
        if rctx.request.path.startswith(self.url):
            static_path = rctx.request.path[len(self.url):]
            while static_path.startswith('/'):
                static_path = static_path[1:]
            file_path = path.join(self.location, static_path)
            if path.exists(file_path) and path.isfile(file_path):
                mime = mimetypes.guess_type(file_path)[0]
                if mime:
                    rctx.response.content_type = mime
                with open(file_path, 'r') as f:
                    rctx.response.write(f.read())
                return rctx.next()
            else:
                raise HttpException(httplib.NOT_FOUND)
        return STOP
