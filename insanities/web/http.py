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
        return path# or '/'

    @property
    def path_qs(self):
        path = super(Request, self).path_qs
        if self._prefixes:
            length = sum(map(len, self._prefixes))
            path = path[length:]
        return path# or '/'

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


class CopyOnUpdateDict(object):
    #TODO: add unitests
    # XXX i don't like this realization

    def __init__(self, **kwargs):
        self._current_data = data = kwargs
        self._stack = [[data, False]]
        self._changed = False

    def commit(self):
        data, changed = self._stack.pop()
        olddata, oldchanged = self._stack.pop()
        self._changed = changed or oldchanged
        self._stack.append([data, changed])

    def rollback(self):
        self._current_data, self._changed = self._stack.pop()

    def lazy_copy(self):
        self._stack.append([self._current_data, False])
        self._changed = False

    def _do_copy(self):
        self._current_data = self._current_data.copy()
        self._stack[-1][0] = self._current_data
        self._stack[-1][1] = self._changed = True

    def __setitem__(self, k, v):
        if not self._changed:
            self._do_copy()
        self._current_data[k] = v

    def __contains__(self, k):
        return k in self._current_data

    def __getitem__(self, k):
        return self._current_data[k]

    def __delitem__(self, k):
        if not self._changed:
            self._do_copy()
        del self._current_data[k]

    def update(self, other):
        if not self._changed:
            self._do_copy()
        self._current_data.update(other)

    def __getattr__(self, name):
        if name in self._current_data:
            return self._current_data[name]
        raise AttributeError(name)

    def get(self, name, default=None):
        return self._current_data.get(name, default)

    def as_dict(self):
        return self._current_data.copy()

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
        self.wsgi_env = wsgi_environ.copy()

        #: this attribute is for views and template data,
        #: for example filter match appends params here.
        self.data = CopyOnUpdateDict()

        #: this is config, static, declarative (key, value)
        self.conf = CopyOnUpdateDict(namespace='')

        #: this storage is for nesecary objects like db session, templates env,
        #: cache, url_for. something like dynamic config values.
        self.vals = CopyOnUpdateDict()

    @classmethod
    def blank(cls, url, **data):
        '''
        Method returning blank rctx. Very useful for testing

        `data` - POST parameters.
        '''
        POST = data if data else None
        env = _Request.blank(url, POST=POST).environ
        return cls(env)

    def _set_map_state(self, _map, i, j):
        self._map = _map
        self._map_i, self._map_j = i, j

    def next(self):
        return self._map.run_handler(self, self._map_i, self._map_j)

    # XXX too much code
    def lazy_copy(self):
        self.data.lazy_copy()
        self.vals.lazy_copy()
        self.conf.lazy_copy()

    def commit(self):
        self.data.commit()
        self.vals.commit()
        self.conf.commit()

    def rollback(self):
        self.data.rollback()
        self.vals.rollback()
        self.conf.rollback()

    #def stop(self): cross import
    #    return STOP

