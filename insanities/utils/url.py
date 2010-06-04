# -*- coding: utf-8 -*-

import urllib
import re
import logging
from urllib import quote, unquote
from webob.multidict import MultiDict

logger = logging.getLogger(__name__)


def urlquote(value):
    return quote(value.encode('utf-8') if isinstance(value, unicode) else str(value))


class URL(object):
    '''
        URL object

        Represents URL with schema, host, port, path (required) and query
        specified.

        `schema`, `host`, `port`, `path` are string objects. `query` is 
        MultiDict or any object accepted by MultiDict's constructor.

        `host`, `path` and `query`'s keys and values can be also unicode strings.

        You can get encoded URL like this::

          url = URL('path', **kwargs)
          str_url = str(url)

        In this case path and query args are encoded by urlencode, while host is
        encoded by idna.
    '''

    def __init__(self, path, query=None, host=None, port=None, schema=None):
        self.path = path
        self.query = MultiDict(query) if query else MultiDict()
        self.host = host or ''
        self.port = port or ''
        self.schema = schema or 'http'

    def _copy(self, **kwargs):
        path = kwargs.pop('path', self.path)
        kw = dict(query=self.query, host=self.host, 
                  port=self.port, schema=self.schema)
        kw.update(kwargs)
        return self.__class__(path, **kw)

    def set(self, **kwargs):
        '''Sets value of URL's query keys to given values'''
        query = self.query.copy()
        for k, v in kwargs.items():
            query[k] = v
        return self._copy(query=query)

    def add(self, **kwargs):
        '''Adds values to URL's query'''
        query = self.query.copy()
        for k, v in kwargs.items():
            query.add(k, v)
        return self._copy(query=query)

    def delete(self, key):
        '''Deletes given key from the URL's query'''
        query = self.query.copy()
        del query[key]
        return self._copy(query=query)

    def getall(self, key):
        '''A proxy method for query.getall'''
        return self.query.getall(key)

    def getone(self, key):
        '''A proxy method for query.getone'''
        return self.query.getone(key)

    def get(self, key, default=None):
        '''A proxy method for query.get'''
        return self.query.get(key, default=default)

    def __str__(self):
        query = ('?' + '&'.join(['%s=%s' % (urlquote(k), urlquote(v)) \
                                for k,v in self.query.iteritems()])  \
                 if self.query else '')
        path = urlquote(self.path)

        if self.host:
            host = self.host.encode('idna')
            port = ':' + self.port if self.port else ''
            return ''.join((self.schema, '://', host, port, path,  query))
        else:
            return path + query

    def get_readable(self):
        '''Gets human-readable representation of the url'''
        query = (u'?' + u'&'.join([u'%s=%s' % (k,v) for k, v in self.query.iteritems()]) \
                 if self.query else '')

        if self.host:
            port = ':' + self.port if self.port else ''
            return u''.join((self.schema, '://', self.host, port, self.path,  query))
        else:
            return self.path + query


    def __repr__(self):
        return '<URL "%s">' % str(self)


class UrlTemplate(object):

    _split_pattern = re.compile(r'(<[^<]*>)')
    _converter_pattern = re.compile(r'''^<
            (?P<converter>[a-zA-Z_][a-zA-Z0-9]+)    # converter name
            (?P<args>\(.*?\))?                      # converter args
            \:?                                     # delimiter
            (?P<variable>[a-zA-Z_][a-zA-Z0-9_]*)?    # variable name
            >$''', re.VERBOSE)
    _static_url_pattern = re.compile(r'^[^<]*?$')

    def __init__(self, template, match_whole_str=True, converters=None):
        self.template = template
        self.match_whole_str = match_whole_str
        self._allowed_converters = self._init_converters(converters)
        self._builder_params = []
        self._converters = {}
        self._pattern = re.compile(self._parse(template))

    def match(self, path):
        m = self._pattern.match(unquote(path))
        if m:
            kwargs = m.groupdict()
            # convert params
            for k,v in kwargs.items():
                conv_name, args = self._converters[k]
                # now we replace converter by class instance
                conv = self._init_converter(conv_name, args)
                try:
                    kwargs[k] = conv.to_python(v)
                except ConvertError, err:
                    logger.debug('ConvertError by "%s", value "%s"' % (err.converter, err.value.encode('utf-8')))
                    return False, {}
            return True, kwargs
        return False, {}

    def _parse(self, url):
        result = r'^'
        parts = self._split_pattern.split(url)
        total_parts = len(parts)
        for i, part in enumerate(parts):
            if part:
                is_url_pattern = self._static_url_pattern.match(part)
                if is_url_pattern:
                    result += re.escape(part)
                    self._builder_params.append(part)
                    continue
                is_converter = self._converter_pattern.match(part)
                if is_converter:
                    converter = is_converter.groupdict()['converter']
                    args = is_converter.groupdict()['args']
                    variable = is_converter.groupdict()['variable']
                    if variable is None:
                        variable = converter
                        converter = 'string'
                    result += '(?P<%s>[a-zA-Z0-9_%%-]+)' % variable
                    self._builder_params.append([variable, converter, args])
                    self._converters[variable] = [converter, args]
                    continue
                raise ValueError('Incorrect url "%s"' % url)
            else:
                if i < total_parts - 1:
                    raise ValueError('Incorrect url "%s"' % url)
        if self.match_whole_str:
            result += '$'
        return result

    def __call__(self, **kwargs):
        result = ''
        for part in self._builder_params:
            if isinstance(part, list):
                var, conv_name, args = part
                conv = self._init_converter(conv_name, args)
                value = kwargs[var]
                result += conv.to_url(value)
            else:
                result += part
        return result

    def _init_converter(self, conv_name, args):
        try:
            conv = self._allowed_converters[conv_name]
        except KeyError:
            raise KeyError('There is no converter named "%s"' % conv_name)
        else:
            if args:
                conv = conv()
            else:
                conv = conv()
        return conv

    def _init_converters(self, converters):
        convs = convs_dict.copy()
        if converters is not None:
            for conv in converters:
                 name = conv.name or conv.__name__
                 convs[name] = conv
        return convs

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.template.encode('utf-8'))


from ..web.urlconvs import ConvertError, convs_dict
