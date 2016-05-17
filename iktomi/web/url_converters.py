# -*- coding: utf-8 -*-
import six

from inspect import isclass
from datetime import datetime

__all__ = ['ConvertError', 'default_converters', 'Converter', 'String',
           'Integer', 'Any', 'Date']



class ConvertError(Exception):
    '''
    Converter should raise ConvertError if the given value does not match
    '''

    @property
    def converter(self):
        return self.args[0]

    @property
    def value(self):
        return self.args[1]


class Converter(object):
    '''A base class for urlconverters'''

    regex = '[.a-zA-Z0-9:@&+$,_%%-]+'
    class NotSet(object): pass
    default = NotSet

    def __init__(self, default=NotSet, regex=None):
        if not default is self.NotSet:
            self.default = default
        if regex is not None:
            self.regex = regex

    def to_python(self, value, env=None):
        '''
        Accepts unicode url part and returns python object.
        Should be implemented in subclasses
        '''
        raise NotImplementedError() # pragma: no cover

    def to_url(self, value):
        '''
        Accepts python object and returns unicode prepared to be used
        in url building.
        Should be implemented in subclasses
        '''
        raise NotImplementedError() # pragma: no cover


class String(Converter):
    '''
    Unquotes urlencoded string::
    '''

    min = 1
    max = None

    def __init__(self, min=None, max=None, **kwargs):
        Converter.__init__(self, **kwargs)
        self.min = min if min is not None else self.min
        self.max = max or self.max

    def to_python(self, value, env=None):
        self.check_len(value)
        return value

    def to_url(self, value):
        if six.PY3 and isinstance(value, bytes):
            raise TypeError() # pragma: no cover, safety check
        return six.text_type(value)

    def check_len(self, value):
        length = len(value)
        if length < self.min or self.max and length > self.max:
            raise ConvertError(self, value)


class Integer(Converter):
    '''
    Extracts integer value from url part.
    '''

    regex = '(?:[1-9]\d*|0)'

    def to_python(self, value, env=None):
        try:
            value = int(value)
        except ValueError:
            raise ConvertError(self, value)
        else:
            return value

    def to_url(self, value):
        if isinstance(value, six.string_types):
            # sometimes it is useful to build fake urls with placeholders,
            # to be replaced in JS to real values
            # For example:
            #     root.item(id="REPLACEME")
            return value
        return str(int(value))


class Any(Converter):
    '''
    Checks if string value is in a list of allowed values and returns that value::

        web.match('/<any(yes,no,"probably, no",maybe):answer>')
    '''

    def __init__(self, *values, **kwargs):
        Converter.__init__(self, **kwargs)
        self.values = values

    def to_python(self, value, env=None):
        if value in self.values:
            return value
        raise ConvertError(self, value)

    def to_url(self, value):
        if six.PY3 and isinstance(value, bytes):
            raise TypeError() # pragma: no cover, safety check
        return six.text_type(value)


class Date(Converter):
    '''
    Converts string to datetime by strptime using given format::

        web.match('/<date(format="%Y.%m.%d"):date>')
    '''

    format = "%Y-%m-%d"

    def __init__(self, format=None, **kwargs):
        Converter.__init__(self, **kwargs)
        if format is not None:
            self.format = format

    def to_python(self, value, env=None):
        try:
            return datetime.strptime(value, self.format).date()
        except ValueError:
            raise ConvertError(self, value)

    def to_url(self, value):
        if isinstance(value, six.string_types):
            # sometimes it is useful to build fake urls with placeholders,
            # to be replaced in JS to real values
            # For example:
            #     root.item(id="REPLACEME")
            return value
        return value.strftime(self.format)


default_converters = {'string': String,
                      'int': Integer,
                      'any': Any,
                      'date': Date}

# assert all defined converters are registered
for item in list(globals().values()):
    if isclass(item) and \
       issubclass(item, Converter) and \
       not item is Converter:
        assert item in default_converters.values(), item

