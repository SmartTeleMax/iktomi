# -*- coding: utf-8 -*-

__all__ = ['HttpException', 'RequestContext', ]

import logging
import httplib
import cgi
from webob import Request as _Request, Response
from webob.multidict import MultiDict, NoVars, UnicodeMultiDict

from ..utils import cached_property

logger = logging.getLogger(__name__)


class HttpException(Exception):
    '''
    Exception forcing :class:`Map <insanities.web.core.Map>` to generate
    :class:`Response` with given status code and Location header (if provided)
    '''
    def __init__(self, status, url=None):
        super(HttpException, self).__init__()
        self.status = int(status)
        self.url = url


class Request(_Request):
    '''
    Patched webob Request class
    '''

    def __init__(self, *args, **kwargs):
        super(Request, self).__init__(*args, **kwargs)
        self._prefixes = []
        self._subdomain = ''

    def add_prefix(self, prefix):
        self._prefixes.append(prefix)

    def add_subdomain(self, subdomain):
        if self._subdomain and subdomain:
            self._subdomain = subdomain + '.' + self._subdomain
        elif subdomain:
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


class DictWithNamespace(object):
    #TODO: add unitests

    def __init__(self, **data):
        self._stack = []
        self._current_data = data
        self._current_ns = ''

    def __setitem__(self, k, v):
        self._current_data[k] = v

    def __contains__(self, k):
        return k in self._current_data

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

    def get(self, name, default=None):
        return self._current_data.get(name, default)

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
    '''
    Context of the request. A class containing request and response objects and
    a number of data containers with request environment and processing data.
    '''

    def __init__(self, wsgi_environ):
        self.request = Request(environ=wsgi_environ, charset='utf8')
        self.response = Response()
        self.response.status = httplib.NOT_FOUND
        self.wsgi_env = wsgi_environ.copy()

        #: this attribute is for views and template data,
        #: for example filter match appends params here.
        self.data = DictWithNamespace()

        #: this is config, static, declarative (key, value)
        self.conf = DictWithNamespace()

        #: this storage is for nesecary objects like db session, templates env,
        #: cache, url_for. something like dynamic config values.
        self.vals = DictWithNamespace()

        # this is mark of main map
        self.main_map = None

    @classmethod
    def blank(cls, url, **data):
        '''
        Method returning blank rctx. Very useful for testing

        `data` - POST parameters.
        '''
        POST = data if data else None
        env = _Request.blank(url, POST=POST).environ
        return cls(env)
