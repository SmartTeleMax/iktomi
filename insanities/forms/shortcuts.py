# -*- coding: utf-8 -*-

import re
from . import convs, widgets, fields


class PasswordConv(convs.Char):

    def from_python(self, value):
        return dict([(field.name, None) for field in self.field.fields])

    def get_default(self):
        return ''

    def to_python(self, value):
        etalon = value[list(value)[0]]
        for field in self.field.fields:
            self._assert(value[field.name] == etalon,
                         'password and confirm mismatch', 'mismatch')
        self._assert(etalon not in (None, '')  or self.null,
                     'password required', 'required')
        return etalon


def PasswordSet(name='password',
                 min_length=3, max_length=200, null=True,
                 password_label=None, confirm_label='confirmmm',
                 **kwargs):
        # class implementation has problem with Fieldset copying:
        # it requires to save all kwargs in object's __dict__
        char = convs.Char(min_length=min_length, max_length=max_length, null=null)
        items = (('pass', password_label), ('conf', confirm_label))
        
        kwargs['fields'] = [fields.Field(subfieldname,
                                         conv=char,
                                         label=label,
                                         widget=widgets.PasswordInput)
                            for subfieldname, label in items]
        kwargs.setdefault('conv', PasswordConv(null=null))
        kwargs.setdefault('template', 'fieldset-line')
        
        return fields.FieldSet(name, get_default=lambda: '', **kwargs)

