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


class DictWithNamespace(object):
    #TODO: add unitests

    def __init__(self, **data):
        self._stack = []
        self._current_data = data
        self._current_ns = ''

    def __setitem__(self, k, v):
        self._current_data[k] = v

    def __getitem__(self, k):
        return self._current_data[k]

    def __delitem__(self, k):
        del self._current_data[k]

    def update(self, other):
        self._current_data.update(other)

    def __getattr__(self, name):
        if name in self._current_data:
            return self._current_data[name]
        raise AttributeError(name)

    def push(self, ns, **data):
        self._stack.append((self._current_ns, self._current_data))
        new_data = self._current_data.copy()
        new_data.update(data)
        self._current_data = new_data
        self._current_ns = self._current_ns + '.' + ns if self._current_ns else ns

    def pop(self):
        ns, data = self._current_ns, self._current_data
        self._current_ns, self._current_data = self._stack.pop()
        return ns, data

    def get_namespace(self, ns):
        for namespace, data in self._stack:
            if ns == namespace:
                return data
        if self._current_ns == ns:
            return self._current_data
        raise ValueError('no namespace "%s"' % ns)

    @property
    def namespace(self):
        return self._current_ns


class RequestContext(object):

    def __init__(self, wsgi_environ):
        self.request = Request(environ=wsgi_environ, charset='utf8')
        self.response = Response()
        self.wsgi_env = wsgi_environ.copy()
        self.template_data = DictWithNamespace()
        self.conf = DictWithNamespace()

    @classmethod
    def blank(cls, url, **data):
        import wsgiref.util
        env = {}
        wsgiref.util.setup_testing_defaults(env)
        env['PATH_INFO'] = url
        return cls(env)
