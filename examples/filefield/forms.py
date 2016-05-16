# -*- coding: utf-8 -*-
#import os

from iktomi.forms import Form, convs, widgets
from iktomi.forms.fields import Field
from iktomi.unstable.forms.files import FileFieldSet, FileFieldSetConv#, \
        #                                      TempUploadedFile

#import cfg


#class MyUploadedFile(TempUploadedFile):
#
#    temp_path = os.path.join(cfg.MEDIA, 'temp')
#    temp_url = '/media/temp/'


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
                     #file_cls=MyUploadedFile,
                     conv=FileFieldSetConv(required=True),
                     widget=FileFieldSet.widget(template='fileinput.html')),
    ]

#class OptionalFileForm(Form):
#
#    fields = [
#        Field('accept', label='I accept the terms of service',
#              conv=convs.Bool(required=True),
#              widget=widgets.CheckBox()),
#        FileFieldSet('file', label='File',
#                     file_cls=MyUploadedFile,
#                     conv=FileFieldSetConv(required=False),
#                     template='fileinput.html'),
#    ]


#class SimpleFileForm(Form):
#    #template='forms/paragraph.html'
#
#    fields = [
#        FileField('file', label='File',
#                  conv=convs.SimpleFile(),
#                  widget=widgets.Widget(template='widgets/file.html')),
#    ]
#
