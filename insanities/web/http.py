# -*- coding: utf-8 -*-

__all__ = ['HttpException', 'RequestContext', ]

import logging
import httplib
import urllib
from webob import Request as _Request, Response, MultiDict

logger = logging.getLogger(__name__)


class HttpException(Exception):
    def __init__(self, status, url=None):
        super(HttpException, self).__init__()
        self.status = int(status)
        self.url = url


class URL(object):
    
    schema = 'http'
    domain = None
    path = '/'
    port = None
    is_absolute = False
    query = MultiDict()
    
    def __init__(self, path, **kwargs):
        self.path = path
        query = kwargs.get('query', MultiDict())
        if not isinstance(query, MultiDict):
            query = MultiDict(query)
        kwargs['query'] = query

        self._kwargs = kwargs
        for key, v in kwargs.items():
            setattr(self, key, v)
    
    def _copy(self, **kwargs):
        path = kwargs.pop('path', self.path)
        kw = self._kwargs.copy()
        kw.update(kwargs)
        return self.__class__(path, **kw)
    
    def add_args(self, **kwargs):
        query = self.query.copy()
        query.update(kwargs)
        return self._copy(query=query)

    def replace_args(self, **kwargs):
        query = self.query.copy()
        for key, v in kwargs.items():
            query[key] = v
        return self._copy(query=query)
    
    def delete_args(self, *args):
        query = self.query.copy()
        for key in args:
            if key in query: del query[key]
        return self._copy(query=query)
    
    def force_absolute(self):
        return self._copy(is_absolute=True)
    
    def __unicode__(self):
        query = '?' + urllib.urlencode(self.query) if self.query else ''
        if self.is_absolute:
            assert self.host
            port = ':' + self.port if self.port else ''
            return ''.join((self.schema, '://', self.domain, port, self.path,  query))
        else:
            return self.path + query

    def __repr__(self):
        return '<URL "%s">' % unicode(self)

class Request(_Request):

    def __init__(self, *args, **kwargs):
        super(Request, self).__init__(*args, **kwargs)
        self._prefixes = []
        self._subdomain = ''

    def add_prefix(self, prefix):
        self._prefixes.append(prefix)

    def add_subdomain(self, subdomain):
        if self._subdomain:
            self._subdomain = subdomain + '.' + self._subdomain
        else:
            self._subdomain = subdomain

    # We need to inject code which works with
    # prefixes
    @property
    def path(self):
        path = super(Request, self).path
        if self._prefixes:
            length = sum(map(len, self._prefixes))
            path = path[length:]
        return path or '/'

    @property
    def path_qs(self):
        path = super(Request, self).path_qs
        if self._prefixes:
            length = sum(map(len, self._prefixes))
            path = path[length:]
        return path or '/'

    @property
    def subdomain(self):
        path = super(Request, self).host.split(':')[0]
        if self._subdomain:
            path = path[:-len(self._subdomain)-1]
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

    def as_dict(self):
        return self._current_data.copy()

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

    def __repr__(self):
        return repr(self._current_data)


class RequestContext(object):

    def __init__(self, wsgi_environ):
        self.request = Request(environ=wsgi_environ, charset='utf8')
        self.response = Response()
        self.response.status = httplib.NOT_FOUND
        self.wsgi_env = wsgi_environ.copy()
        #XXX: it may be not good idea to put self in template_data
        self.template_data = DictWithNamespace(rctx=self)
        self.conf = DictWithNamespace()
        # this is mark of main map
        self.main_map = None

    @classmethod
    def blank(cls, url, **data):
        POST = data if data else None
        env = _Request.blank(url, POST=POST).environ
        return cls(env)
