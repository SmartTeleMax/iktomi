# -*- coding: utf-8 -*-

from inspect import isclass


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
        raise NotImplemented()

    def to_url(self, value):
        '''
        Accepts python object and returns unicode prepared to be used
        in url building.

        Should be implemented in subclasses
        '''
        raise NotImplemented()


class String(Converter):
    '''
    Unquotes urlencoded string.

    The converter's name is 'string'
    '''

    name='string'

    def to_python(self, value, **kwargs):
        return value

    def to_url(self, value):
        return str(value)


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
            return 'true'
        return 'false'


convs_dict = dict((item.name or item.__name__, item) \
                  for item in globals().values() \
                  if isclass(item) and issubclass(item, Converter))
