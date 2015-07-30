# -*- coding: utf-8 -*-

from . import shortcuts, convs, widgets_json as widgets
from form_json import Field, FieldSet

def PasswordSet(name='password',
                 min_length=3, max_length=200, required=False,
                 password_label=None, confirm_label='confirm', filters=(),
                 **kwargs):
        # class implementation has problem with Fieldset copying:
        # it requires to save all kwargs in object's __dict__
        char = convs.Char(convs.length(min_length, max_length), *filters,
                          **dict(required=required))
        items = (('pass', password_label), ('conf', confirm_label))
        kwargs['fields'] = [Field(subfieldname,
                                  conv=char,
                                  label=label,
                                  widget=widgets.PasswordInput)
                            for subfieldname, label in items]
        kwargs.setdefault('conv', shortcuts.PasswordConv(required=required))
        kwargs.setdefault('widget', widgets.FieldSetWidget)
        return FieldSet(name, get_initial=lambda: '', **kwargs)

