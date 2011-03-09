# -*- coding: utf-8 -*-

import urllib
import re
import logging
import urllib
from inspect import isclass
from webob.multidict import MultiDict

logger = logging.getLogger(__name__)


def urlquote(value):
    return urllib.quote(value.encode('utf-8') if isinstance(value, unicode) else str(value))


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

    def __new__(cls, path, query=None, host=None, port=None, schema=None):
        '''
        path - urlencoded string or unicode object (not encoded at all)
        '''
        path = path if isinstance(path, str) else urlquote(path)
        query = MultiDict(query) if query else MultiDict()
        host = host or ''
        port = port or ''
        schema = schema or 'http'
        self = str.__new__(cls, construct_url(path, query, host, 
                                              port,schema))
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


class ConvertError(Exception):

    @property
    def converter(self):
        return self.args[0]

    @property
    def value(self):
        return self.args[1]


class Converter(object):
    '''A base class for urlconverters'''

    #: A key significating what converter is used in particular url template
    name=None

    def to_python(self, value, **kwargs):
        '''
        Accepts unicode url part and returns python object.
        Should be implemented in subclasses
        '''
        raise NotImplementedError()

    def to_url(self, value):
        '''
        Accepts python object and returns unicode prepared to be used
        in url building.
        Should be implemented in subclasses
        '''
        raise NotImplementedError()


class String(Converter):
    '''
    Unquotes urlencoded string.

    The converter's name is 'string'
    '''

    name='string'

    def to_python(self, value, **kwargs):
        return value

    def to_url(self, value):
        return unicode(value)


class Integer(Converter):
    '''
    Extracts integer value from url part.

    The converter's name is 'int'
    '''

    name='int'

    def to_python(self, value, **kwargs):
        try:
            value = int(value)
        except ValueError:
            raise ConvertError(self.name, value)
        else:
            return value

    def to_url(self, value):
        return str(value)


class Boolean(Converter):
    '''
    Translates on/off, true/false, True/False, yes/no strings to python bool.

    The converter's name is 'bool'.
    '''

    name='bool'
    _true = ['on', 'true', 'True', 'yes']
    _false = ['off', 'false', 'False', 'no']

    def to_python(self, value, **kwargs):
        if value in self._true:
            return True
        elif value in self._false:
            return False
        raise ConvertError(self.name, value)

    def to_url(self, value):
        if value:
            return 'yes'
        return 'no'


class Any(Converter):
    name='any'
    def __init__(self, *values):
        self.values = values

    def to_python(self, value, **kwargs):
        if value in self.values:
            return value
        raise ConvertError(self.name, value)


convs_dict = dict((item.name or item.__name__, item) \
                  for item in globals().values() \
                  if isclass(item) and issubclass(item, Converter))


_split_pattern = re.compile(r'(<[^<]*>)')

#NOTE: taken from werkzeug
_converter_pattern = re.compile(r'''^<
        (?P<converter>[a-zA-Z_][a-zA-Z0-9]+)    # converter name
        (?:\((?P<args>.*?)\))?                  # converter args
        \:?                                     # delimiter
        (?P<variable>[a-zA-Z_][a-zA-Z0-9_]*)?   # variable name
        >$''', re.VERBOSE | re.U)

_static_url_pattern = re.compile(r'^[^<]*?$')

def construct_re(url_template, match_whole_str=False, converters=None,
                 default_converter='string'):
    '''
    url_template - str or unicode representing template

    Constructed pattern expects urlencoded string!

    returns  (compiled re pattern, 
              dict {url param name: [converter name, converter args (str)]},
              list of (variable name, converter name, converter args name))
    '''
    converters = converters or {}
    converters.update(convs_dict)
    # needed for reverse url building (or not needed?)
    builder_params = []
    # found url params and their converters
    url_params = {}
    result = r'^'
    parts = _split_pattern.split(url_template)
    total_parts = len(parts)
    for i, part in enumerate(parts):
        if part:
            is_url_pattern = _static_url_pattern.match(part)
            if is_url_pattern:
                #NOTE: right order:
                #      - make part str if it was unicode
                #      - urlquote part
                #      - escape all specific for re chars in part
                part = urlquote(unicode(part).encode('utf-8'))
                result += re.escape(part)
                builder_params.append(part)
                continue
            is_converter = _converter_pattern.match(part)
            if is_converter:
                converter = is_converter.groupdict()['converter']
                args = is_converter.groupdict()['args']
                variable = is_converter.groupdict()['variable']
                if variable is None:
                    variable = converter
                    converter = default_converter
                result += '(?P<%s>[.a-zA-Z0-9_%%-]+)' % variable
                try:
                    conv_object = init_converter(converters[converter], args)
                except KeyError:
                    raise KeyError('There is no converter named "%s"' % converter)
                builder_params.append((variable, conv_object))
                url_params[variable] = conv_object
                continue
            raise ValueError('Incorrect url template "%s"' % url_template)
        else:
            if i < total_parts - 1:
                raise ValueError('Incorrect url template "%s"' % url_template)
    if match_whole_str:
        result += '$'
    return re.compile(result), url_params, builder_params


def init_converter(conv_class, args):
    if args:
        #XXX: taken from werkzeug
        storage = type('_Storage', (), {'__getitem__': lambda s, x: x})()
        args, kwargs = eval(u'(lambda *a, **kw: (a, kw))(%s)' % args, {}, storage)
        return conv_class(*args, **kwargs)
    return conv_class()


class UrlTemplate(object):

    def __init__(self, template, match_whole_str=True, converters=None,
                 default_converter='string'):
        self.template = template
        self.match_whole_str = match_whole_str
        self._allowed_converters = self._init_converters(converters)
        self._pattern, self._url_params, self._builder_params = construct_re(template, 
                                                                             match_whole_str=match_whole_str,
                                                                             converters=self._allowed_converters,
                                                                             default_converter=default_converter)

    def match(self, path, **kw):
        '''
        path - str (urlencoded)
        '''
        m = self._pattern.match(path)
        if m:
            kwargs = m.groupdict()
            # convert params
            for url_arg_name, value_urlencoded in kwargs.items():
                conv_obj = self._url_params[url_arg_name]
                unicode_value = urllib.unquote(value_urlencoded).decode('utf-8', 'replace')
                try:
                    kwargs[url_arg_name] = conv_obj.to_python(unicode_value, **kw)
                except ConvertError, err:
                    logger.debug('ConvertError by "%s", value "%s"' % (err.converter, err.value.encode('utf-8')))
                    return False, {}
            return True, kwargs
        return False, {}

    def __call__(self, **kwargs):
        'Url building with url params values taken from kwargs. (reverse)'
        result = ''
        for part in self._builder_params:
            if isinstance(part, tuple):
                var, conv_obj = part
                value = kwargs[var]
                result += urlquote(conv_obj.to_url(value))
            else:
                result += part
        # result - urlencoded str
        return result

    def _init_converters(self, converters):
        convs = convs_dict.copy()
        if converters is not None:
            for conv in converters:
                 name = conv.name or conv.__name__.lower()
                 convs[name] = conv
        return convs

    def __repr__(self):
        return '%s(%r, match_whole_str=%r)' % (self.__class__.__name__, 
                                               self.template.encode('utf-8'),
                                               self.match_whole_str)
