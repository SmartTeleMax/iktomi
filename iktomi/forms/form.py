# -*- coding: utf-8 -*-

from time import time
import struct, os, itertools

from webob.multidict import MultiDict
from ..utils import weakproxy, cached_property

from . import convs
from .perms import DEFAULT_PERMISSIONS
from .media import FormMedia


class FormEnvironment(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)


class FormValidationMetaClass(type):
    '''
    Metaclass to assert that some obsolete methods are not used.
    can be removed from iktomi after all existing code is cleaned up.
    '''

    def __new__(mcs, name, bases, dict_):
        if any([x.startswith('clean__') for x in dict_]):
            raise TypeError('Form clean__ methods are obsolete')
        return type.__new__(mcs, name, bases, dict_)


class Form(object):

    template = 'forms/default'
    media = FormMedia()
    permissions = DEFAULT_PERMISSIONS
    __metaclass__ = FormValidationMetaClass

    def __init__(self, env=None, initial=None, name=None, permissions=None):
        env = env or {}
        initial = initial or {}
        self.env = FormEnvironment(**env) if isinstance(env, dict) else env
        self.name = name
        self.raw_data = MultiDict()
        # NOTE: `initial` is used to set initial display values for fields.
        #       If you provide initial value for some aggregated field
        #       you need to provide values for all fields that are in that
        #       aggregated field, including `None` as empty values.
        self.initial = initial
        self.python_data = initial.copy()
        # clone all fields
        self.fields = [field(parent=self) for field in self.fields]

        if permissions is None:
            permissions = self.permissions
        self.permissions = set(permissions)

        for field in self.fields:
            # NOTE: we do not put `get_initial()` call result in `self.initial`
            #       because it may differ for each call
            value = initial.get(field.name, field.get_initial())
            self.python_data[field.name] = value
            field.set_raw_value(self.raw_data,
                                field.from_python(value))
        self.errors = {}

    @cached_property
    def id(self):
        '''Random ID for given form input'''
        # Time part is repeated in about 3 days period
        time_part = struct.pack('!d', time())[3:]
        return ('form'+time_part+os.urandom(1)).encode('hex')

    @property
    def form(self):
        return self

    @property
    def prefix(self):
        '''A prefix for names of field inputs'''
        if self.name:
            return self.name+':'
        else:
            return ''

    def render(self):
        '''Proxy method to form's environment render method'''
        return self.env.template.render(self.template, form=self)

    @property
    def is_valid(self):
        '''Is true if validated form as no errors'''
        return not self.errors

    def get_media(self):
        '''
        Returns a list of FormMedia objects related to the form and
        all of it's fields
        '''
        media = FormMedia(self.media, env=self.env)
        for field in self.fields:
            media += field.widget.get_media()
        return media

    def accept(self, data):
        self.raw_data = MultiDict(data)
        self.errors = {}
        for field in self.fields:
            if field.writable:
                self.python_data[field.name] = field.accept()
            else:
                # readonly field
                value = self.python_data[field.name]
                field.set_raw_value(self.raw_data, field.from_python(value))
        return self.is_valid

    def get_field(self, name):
        '''
        Gets field by input name
        '''
        names = name.split('.', 1)
        for field in self.fields:
            if field.name == names[0]:
                if len(names) > 1:
                    return field.get_field(names[1])
                return field
        return None

    def get_data(self, compact=True):
        '''
        Returns data representing current state of the form. While
        Form.raw_data may contain alien fields and invalid data, this method
        returns only valid fields that belong to this form only. It's designed
        to pass somewhere current state of the form (as query string or by
        other means).
        '''
        data = MultiDict()
        for field in self.fields:
            raw_value = field.from_python(self.python_data[field.name])
            field.set_raw_value(data, raw_value)
        if compact:
            data = MultiDict([(k, v) for k, v in data.items() if v])
        return data
