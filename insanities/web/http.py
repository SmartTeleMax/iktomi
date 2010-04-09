# -*- coding: utf-8 -*-

__all__ = ['HttpException', 'RequestContext', ]

import logging
from webob import Request as _Request, Response

logger = logging.getLogger(__name__)


class HttpException(Exception):
    def __init__(self, status, url=None):
        super(HttpException, self).__init__()
        self.status = int(status)
        self.url = url


class Request(_Request):

    def __init__(self, *args, **kwargs):
        super(Request, self).__init__(*args, **kwargs)
        self._prefixes = []

    def add_prefix(self, prefix):
        self._prefixes.append(prefix)

    # We need to inject code which works with
    # prefixes
    @property
    def path(self):
        path = super(Request, self).path
        if self._prefixes:
            length = sum(map(len, self._prefixes))
            path = path[length:]
        if not path:
            path = '/'
        return path

    @property
    def path_qs(self):
        path = super(Request, self).path_qs
        if self._prefixes:
            length = sum(map(len, self._prefixes))
            path = path[length:]
        if not path:
            path = '/'
        return path


class RequestContext(object):

    def __init__(self, wsgi_environ, url_for=None, data=None):
        self.request = Request(environ=wsgi_environ, charset='utf8')
        self.response = Response()
        self.wsgi_env = wsgi_environ.copy()
        self.__data = data or {}
        self._main_map = None
        self.__url_for = url_for

    def add_data(self, **kwargs):
        logger.debug('rctx.add_data(): %r' % kwargs)
        self.__data.update(kwargs)

    @property
    def data(self):
        return self.__data

    @property
    def url_for(self):
        if self.__url_for is None:
            raise ValueError('No reverse url function was '
                             'provided to RequestContext')
        return self.__url_for
