# -*- coding: utf-8 -*-

__all__ = ['URL']

import urllib
from urlparse import urlparse, parse_qs
from webob.multidict import MultiDict
from .url_templates import urlquote


def construct_url(path, query, host, port, schema):
    query = ('?' + '&'.join(['%s=%s' % (urlquote(k), urlquote(v)) \
                            for k,v in query.iteritems()])  \
             if query else '')

    path = path
    if host:
        host = host.encode('idna')
        port = ':' + port if port else ''
        return ''.join((schema, '://', host, port, path,  query))
    else:
        return path + query


class URL(str):

    def __new__(cls, path, query=None, host=None, port=None, schema=None, show_host=True):
        '''
        path - urlencoded string or unicode object (not encoded at all)
        '''
        path = path if isinstance(path, str) else urlquote(path)
        query = MultiDict(query) if query else MultiDict()
        host = host or ''
        port = port or ''
        schema = schema or 'http'
        self = str.__new__(cls, construct_url(path, query, host if show_host else '', port,schema))
        self.path = path
        self.query = query
        self.host = host
        self.port = port
        self.schema = schema
        self.show_host = show_host
        return self

    @classmethod
    def from_url(cls, url, show_host=True):
        '''Parse string and get URL instance'''
        # url must be idna-encoded and url-quotted
        url = urlparse(url)
        query = sum([[(k.decode('utf-8'), v.decode('utf-8'))
                      for v in values]
                     for k, values in parse_qs(url.query).items()], [])
        host = url.netloc.split(':', 1)[0] if ':' in url.netloc else url.netloc
        port = url.netloc.split(':')[1] if ':' in url.netloc else ''
        return cls(urllib.unquote(url.path).decode('utf-8'),
                   query, host.decode('idna'),
                   port, url.scheme, show_host)

    def _copy(self, **kwargs):
        path = kwargs.pop('path', self.path)
        kw = dict(query=self.query, host=self.host, 
                  port=self.port, schema=self.schema,
                  show_host=self.show_host)
        kw.update(kwargs)
        return self.__class__(path, **kw)

    def qs_set(self, *args, **kwargs):
        '''Set values in QuerySet MultiDict'''
        if args and kwargs:
            raise TypeError('Use positional args or keyword args not both')
        query = self.query.copy()
        if args:
            mdict = MultiDict(args[0])
            for k in mdict.keys():
                if k in query:
                    del query[k]
            for k, v in mdict.items():
                query.add(k, v)
        else:
            for k, v in kwargs.items():
                query[k] = v
        return self._copy(query=query)

    def qs_add(self, *args, **kwargs):
        '''Add value to QuerySet MultiDict'''
        query = self.query.copy()
        if args:
            mdict = MultiDict(args[0])
            for k, v in mdict.items():
                query.add(k, v)
        for k, v in kwargs.items():
            query.add(k, v)
        return self._copy(query=query)

    def with_host(self):
        '''Force show_host parameter'''
        return self._copy(show_host=True)

    def qs_delete(self, key):
        '''Delete value from QuerySet MultiDict'''
        query = self.query.copy()
        try:
            del query[key]
        except KeyError:
            pass
        return self._copy(query=query)

    def qs_get(self, key, default=None):
        '''Get a value from QuerySet MultiDict'''
        return self.query.get(key, default=default)

    def get_readable(self):
        '''Gets human-readable representation of the url (as unicode string)'''
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
