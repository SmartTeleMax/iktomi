# -*- coding: utf-8 -*-
import os

from insanities.forms import *
from insanities.forms.ui import widgets
from insanities.ext.filefields import TempFile, TempFileWidget

import cfg


class FileForm(Form):

    widget = widgets.FormWidget

    fields = [
        Field('accept', label='I accept the terms of service',
              conv=convs.Bool(required=True),
              widget=widgets.CheckBox()),
        FileField('file', label='File',
                  conv=TempFile(temp_dir=os.path.join(cfg.MEDIA, 'temp'),
                                required=True,
                                temp_url='/media/temp/'),
                  widget=TempFileWidget),
    ]

