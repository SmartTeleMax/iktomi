# -*- coding: utf-8 -*-
import os

from insanities.forms import *
from insanities.forms import widgets
from insanities.ext.filefields import TempFile, TempFileWidget, TempFileField

import cfg


class FileForm(Form):
    template='forms/paragraph.html'

    fields = [
        Field('accept', label='I accept the terms of service',
              conv=convs.Bool(required=True),
              widget=widgets.CheckBox()),
        TempFileField('file', label='File',
                      conv=TempFile(temp_dir=os.path.join(cfg.MEDIA, 'temp'),
                                    required=True,
                                    temp_url='/media/temp/'),
                      widget=TempFileWidget(template='fileinput.html')),
    ]


class SimpleFileForm(Form):
    template='forms/paragraph.html'

    fields = [
        FileField('file', label='File',
                      conv=convs.SimpleFile(),
                      widget=widgets.Widget(template='fileinput.html')),
    ]

