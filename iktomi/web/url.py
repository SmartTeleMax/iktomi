# -*- coding: utf-8 -*-

__all__ = ['URL']

import six
if six.PY2:
    from urlparse import urlparse, parse_qs, unquote
else:# pragma: no cover; we check coverage only in python2 part
    from urllib.parse import urlparse, parse_qs, unquote
from webob.multidict import MultiDict
from .url_templates import urlquote
from iktomi.utils.url import uri_to_iri_parts


def construct_url(path, query, host, port, schema, fragment=None):
    query = ('?' + '&'.join('{}={}'.format(urlquote(k), urlquote(v))
                            for k, v in six.iteritems(query))
             if query else '')

    hash_part = ('#' + fragment) if fragment is not None else ''

    if host:
        host = host.encode('idna').decode('utf-8')
        port = ':' + port if port else ''
        return ''.join((schema, '://', host, port, path,  query, hash_part))
    else:
        return path + query + hash_part

if six.PY2:
    def _parse_qs(query):
        return sum([[(k.decode('utf-8', errors="replace"),
                      v.decode('utf-8', errors="replace"))
                     for v in values]
                    for k, values in parse_qs(query).items()], [])

    def _unquote(path):
        # in PY2 unquote returns encoded value of the type it has accepted
        return unquote(path.encode('utf-8')).decode('utf-8')
else:# pragma: no cover
    def _parse_qs(query):
        return sum([[(k, v) for v in values]
                     for k, values in parse_qs(query).items()], [])

    # in PY3 is accepts and returns decoded str
    _unquote = unquote

# Note: you should probably not use unicode in fragment part of URL.
#       We encode it according to RFC, but different client handle
#       it in different ways: Chrome allows unicode and does not 
#       encode/decode it at all, while Firefox handles it according RFC
def _decode_path(path):
    if path is None:
        return None
    if isinstance(path, six.binary_type):
        path = path.decode('utf-8', errors="replace") # XXX
    path = urlquote(path)
    return path


class URL(str):

    # as for now:
    #     path - urlencoded string of text_type (not bytes)
    #     host - unicode idna-decoded
    #     query - dict of unicode keys and unicode or implementing
    #             string convertion values
    #     fragment - None or urlencoded string of text_type

    def __new__(cls, path=None, query=None, host=None, port=None, schema=None,
                fragment=None, show_host=True, uri_path=None, uri_fragment=None):
        '''
        path - urlencoded string or unicode object (not encoded at all)
        '''
        path = uri_path or _decode_path(path)
        fragment = uri_fragment or _decode_path(fragment)
        query = MultiDict(query) if query else MultiDict()
        host = host or ''
        port = port or ''
        schema = schema or 'http'
        _self = construct_url(path, query, host if show_host else '',
                              port, schema, fragment)
        self = str.__new__(cls, _self)
        self.path = path
        self.query = query

        # force decode idna from both encoded and decoded input
        self.host = host.encode('idna').decode('idna')
        self.port = port
        self.schema = schema
        self.fragment = fragment
        self.show_host = show_host
        return self


    @classmethod
    def from_url(cls, url, show_host=True):
        '''Parse string and get URL instance'''
        # url must be idna-encoded and url-quotted

        if six.PY2:
            if isinstance(url, six.text_type):
                url = url.encode('utf-8')
            parsed = urlparse(url)
            netloc = parsed.netloc.decode('utf-8') # XXX HACK
        else:# pragma: no cover
            if isinstance(url, six.binary_type):
                url = url.decode('utf-8', errors='replace') # XXX
            parsed = urlparse(url)
            netloc = parsed.netloc

        query = _parse_qs(parsed.query)
        host = netloc.split(':', 1)[0] if ':' in netloc else netloc

        port = netloc.split(':')[1] if ':' in netloc else ''
        path = unquote(parsed.path)
        fragment = unquote(parsed.fragment)
        if not fragment and not url.endswith('#'):
            fragment = None
        return cls(path,
                   query, host,
                   port, parsed.scheme, fragment, show_host)

    def _copy(self, **kwargs):
        kw = dict(query=self.query, host=self.host,
                  port=self.port, schema=self.schema,
                  show_host=self.show_host)
        kw.update(kwargs)
        if 'path' not in kw:
            kw['uri_path'] = self.path
        if 'fragment' not in kw:
            kw['uri_fragment'] = self.fragment
        return self.__class__(**kw)

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

    def qs_delete(self, *keys):
        '''Delete value from QuerySet MultiDict'''
        query = self.query.copy()
        for key in set(keys):
            try:
                del query[key]
            except KeyError:
                pass
        return self._copy(query=query)

    def qs_get(self, key, default=None):
        '''Get a value from QuerySet MultiDict'''
        return self.query.get(key, default=default)

    def get_readable(self):
        '''
        Gets human-readable representation of the url (as unicode string,
        IRI according RFC3987)
        '''
        query = (u'?' + u'&'.join(u'{}={}'.format(urlquote(k), urlquote(v))
                                  for k, v in six.iteritems(self.query))
                 if self.query else '')
        hash_part = (u'#' + self.fragment) if self.fragment is not None else u''

        path, query, hash_part = uri_to_iri_parts(self.path, query, hash_part)

        if self.host:
            port = u':' + self.port if self.port else u''
            return u''.join((self.schema, '://', self.host, port, path,  query, hash_part))
        else:
            return path + query + hash_part

    def __repr__(self):
        return '<URL {!r}>'.format(str(self))
