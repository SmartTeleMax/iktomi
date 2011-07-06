# -*- coding: utf-8 -*-

__all__ = ['Reverse', 'URL']

import urllib
from webob.multidict import MultiDict
from .url import construct_url, urlquote


class URL(str):
    def __new__(cls, path, query=None, host=None, port=None, schema=None):
        '''
        path - urlencoded string or unicode object (not encoded at all)
        '''
        path = path if isinstance(path, str) else urlquote(path)
        query = MultiDict(query) if query else MultiDict()
        host = host or ''
        port = port or ''
        schema = schema or 'http'
        self = str.__new__(cls, construct_url(path, query, host, port,schema))
        self.path = path
        self.query = query
        self.host = host
        self.port = port
        self.schema = schema
        return self

    def _copy(self, **kwargs):
        path = kwargs.pop('path', self.path)
        kw = dict(query=self.query, host=self.host, 
                  port=self.port, schema=self.schema)
        kw.update(kwargs)
        return self.__class__(path, **kw)

    def qs_set(self, **kwargs):
        query = self.query.copy()
        for k, v in kwargs.items():
            query[k] = v
        return self._copy(query=query)

    def qs_add(self, **kwargs):
        query = self.query.copy()
        for k, v in kwargs.items():
            query.add(k, v)
        return self._copy(query=query)

    def qs_delete(self, key):
        query = self.query.copy()
        del query[key]
        return self._copy(query=query)

    def qs_get(self, key, default=None):
        return self.query.get(key, default=default)

    def qs_getall(self, key):
        return self.query.getall(key)

    def qs_getone(self, key):
        return self.query.getone(key)

    def get_readable(self):
        '''Gets human-readable representation of the url'''
        query = (u'?' + u'&'.join([u'%s=%s' % (k,v) for k, v in self.query.iteritems()]) \
                 if self.query else '')

        path = urllib.unquote(self.path).decode('utf-8')
        if self.host:
            port = u':' + self.port if self.port else u''
            return u''.join((self.schema, '://', self.host, port, path,  query))
        else:
            return path + query

    def __repr__(self):
        return '<URL %r>' % str.__repr__(self)


class Reverse(object):
    def __init__(self, locations=None, builder=None, builder_kwargs=None):
        self._locations = locations or {}
        self._builder = builder
        self._builder_kwargs = builder_kwargs or {}

    def _copy(self, **kw):
        vars = dict(locations=self._locations, 
                    builder=self._builder, 
                    builder_kwargs=self._builder_kwargs)
        vars.update(kw)
        return self.__class__(**vars)

    def __call__(self, **kwargs):
        return self._copy(builder_kwargs=kwargs)

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        if name in self._locations:
            value = self._locations[name]
            return self._copy(locations=value[1], builder=value[0])
        raise AttributeError(name)

    def __str__(self):
        if self._builder:
            host = u'.'.join(self._builder.subdomains)
            # path - urlencoded str
            path = ''.join([b(**self._builder_kwargs) for b in self._builder.builders])
            return URL(path, host=host)
        return URL('')

    @classmethod
    def from_handler(cls, handler, env=None):
        from .core import locations
        return cls(locations(handler))
