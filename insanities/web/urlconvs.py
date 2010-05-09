# -*- coding: utf-8 -*-

from urllib import quote, unquote
from inspect import isclass


class ConvertError(Exception):

    @property
    def converter(self):
        return self.args[0]

    @property
    def value(self):
        return self.args[1]


class Converter(object):

    name=None

    def to_python(self, value):
        raise NotImplemented()

    def to_url(self, value):
        raise NotImplemented()


class String(Converter):

    name='string'

    def to_python(self, value):
        return unquote(value)

    def to_url(self, value):
        return quote(str(value))


class Integer(Converter):

    name='int'

    def to_python(self, value):
        try:
            value = int(unquote(value))
        except ValueError:
            raise ConvertError(self.name, value)
        else:
            return value

    def to_url(self, value):
        return quote(str(value))


class Boolean(Converter):

    name='bool'
    _true = ['on', 'true', 'True', 'yes']
    _false = ['off', 'false', 'False', 'no']

    def to_python(self, value):
        value = unquote(value)
        if value in self._true:
            return True
        elif value in self._false:
            return False
        raise ConvertError(self.name, value)

    def to_url(self, value):
        if value:
            return 'true'
        return 'false'


convs_dict = dict((item.name or item.__name__, item) \
                  for item in globals().values() \
                  if isclass(item) and issubclass(item, Converter))
