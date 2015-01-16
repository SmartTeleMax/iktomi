# -*- coding: utf-8 -*-
import logging
import json
from collections import OrderedDict

from .form import Form
from .fields import Field, FieldSet, FieldBlock, FieldList
from . import widgets_json


logger = logging.getLogger(__name__)


class JSONForm(Form):

    template = None

    def __init__(self, env=None, initial=None, name=None, permissions=None):
        initial = initial or {}
        self.env = env
        self.name = name
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
            self.python_data.update(field.load_initial(initial))
        self.errors = {}
        self.raw_value = self.get_data()

    def get_data(self):
        data = {}
        for field in self.fields:
            data.update(field.get_data())
        return data

    def render(self):
        js = {'data': self.get_data(),
              'errors': self.errors,
              'widgets': [x.widget.render() for x in self.fields]}
        return json.dumps(js)

    def accept(self, data):
        '''
        Try to accept dict-like object and return if it is valid.
        '''
        self.raw_value = dict(data)
        self.errors = {}
        for field in self.fields:
            if field.writable:
                value = self.raw_value.get(field.name) \
                            if field.name \
                            else self.raw_value
                self.python_data.update(field.accept(value))
            else:
                # readonly field
                self.raw_value.update(field.get_data())
        return self.is_valid


class BaseJSONField(object):

    raw_value = None

    def load_initial(self, initial):
        value = initial.get(self.name, self.get_initial())
        return {self.name: value}


class JSONField(BaseJSONField, Field):

    widget = widgets_json.TextInput()
    set_raw_value = None
    from_python = None

    def get_data(self):
        if self.error and self.writable:
            value = self.raw_value
        else:
            value = self.conv.from_python(self.clean_value)
        return {self.name: value}

    def accept(self, raw_value):
        self.raw_value = raw_value
        if not self._check_value_type(raw_value):
            # XXX should this be silent or TypeError?
            raw_value = [] if self.multiple else self._null_value
        self.clean_value = self.conv.accept(raw_value)
        return {self.name: self.clean_value}


class _JSONFieldSet(object):

    def accept(self, raw_value):
        if not isinstance(raw_value, dict):
            raw_value = {} # XXX
        self.raw_value = raw_value

        result = dict(self.python_data)
        for field in self.fields:
            if field.writable:
                value = self.raw_value.get(field.name) \
                            if field.name \
                            else self.raw_value
                result.update(field.accept(value))
            else:
                self.raw_value.update(field.get_data())
                # readonly field
                #field.set_raw_value(self.form.raw_value,
                #                    field.from_python(result[field.name]))
        self.clean_value = self.conv.accept(result)
        return {self.name: self.clean_value}


class JSONFieldSet(_JSONFieldSet, BaseJSONField, FieldSet):

    widget = widgets_json.FieldSetWidget()
    set_raw_value = None

    def get_data(self):
        data = {}
        for field in self.fields:
            data.update(field.get_data())
        return {self.name: data}


class JSONFieldBlock(_JSONFieldSet, BaseJSONField, FieldBlock):

    widget = widgets_json.FieldBlockWidget()

    def accept(self, raw_value):
        _JSONFieldSet.accept(self, raw_value)
        return self.clean_value

    def load_initial(self, initial):
        result = {}
        for field in self.fields:
            result.update(field.load_initial(initial))
        return result

    def get_data(self):
        data = {}
        for field in self.fields:
            data.update(field.get_data())
        return data


class JSONFieldList(BaseJSONField, FieldList):

    widget = widgets_json.FieldListWidget()
    set_raw_value = False
    indices_input_name = None

    def accept(self, raw_values):
        old = self.python_data
        if not isinstance(raw_values, list):
            raw_values = []
        self.raw_value = raw_values

        result = OrderedDict()
        for raw_value in raw_values:
            index = result.get('_key', '')
            try:
                #XXX: we do not convert index to int, just check it.
                #     is it good idea?
                int(index)
            except ValueError:
                logger.warning('Got incorrect index from form: %r', index)
                continue

            #TODO: describe this
            field = self.field(name=str(index))
            if not field.writable:
                # readonly field
                if index in old:
                    result[field.name] = old[field.name]
            else:
                result.update(field.accept(raw_value))
        self.clean_value = self.conv.accept(result)
        return {self.name: self.clean_value}


    def get_data(self):
        data = []
        for index in self.python_data:
            field = self.field(name=str(index))
            data.append(dict(field.get_data(),
                             _key=int(index)))
        return data

Form = JSONForm
Field = JSONField
FieldSet = JSONFieldSet
FieldList = JSONFieldList
FieldBlock = JSONFieldBlock
