# -*- coding: utf-8 -*-

from insanities.forms import *


class PostForm(Form):
    fields = [
        Field('title', label='title',
              conv=convs.Char(min_length=3, max_length=255)),
        Field('body', label='body',
              conv=convs.Char(min_length=3, max_length=4000),
              widget=widgets.Textarea()),
    ]

