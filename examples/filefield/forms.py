# -*- coding: utf-8 -*-

from iktomi.forms import Form, convs, widgets
from iktomi.forms.fields import Field
from iktomi.unstable.forms.files import FileFieldSet, FileFieldSetConv


def check_terms(conv, value):
    if not value:
        raise convs.ValidationError('Please, accept the terms os service')
    return value


class FileForm(Form):

    fields = [
        Field('accept',
              label='I accept the terms of service',
              conv=convs.Bool(check_terms),
              widget=widgets.CheckBox()),
        FileFieldSet('file', label='File',
                     conv=FileFieldSetConv(required=True),
                     widget=FileFieldSet.widget(template='fileinput.html')),
    ]

