# -*- coding: utf-8 -*-
import logging
from iktomi.forms import convs, widgets
from ..forms.fields import Field, FieldSet, FileField

logger = logging.getLogger(__name__)


class FileFieldSetConv(convs.Converter):

    error_inner = 'Error uploading file'
    error_lost = 'Transient file has been lost'

    def from_python(self, value):
        return {'temp_name': value.filename if value and value.mode == 'temp' else None,
                'original_name': value and value.original_name,
                'file': value,
                'mode': value.mode if value is not None else 'empty'}

    def _to_python(self, file=None, mode=None, temp_name=None, original_name=None):

        if not self._is_empty(file):
            file = self.env.media_file_manager.make_transient_from_fs(file)
        else:
            file = None

        if mode == 'delete':
            if self.required:
                raise convs.ValidationError(self.error_required)
            return None

        if mode == 'empty':
            if not file and self.required:
                raise convs.ValidationError(self.error_required)

        elif mode == 'temp':
            if not original_name:
                logger.warning('Missing original_name for FileField')
            if not temp_name:
                logger.warning('Missing temp_name for FileField in mode "temp"')
                raise convs.ValidationError(self.hacking)

            try:
                temp_file = self.env.media_file_manager.restore_transient(temp_name)
            except Exception: # XXX what kind of exception?
                raise convs.ValidationError(self.error_lost)

            if file:
                temp_file.delete()
            else:
                file = temp_file

        elif mode == 'existing':
            if not file:
                return self._existing_value
        else:
            logger.warning('Unknown mode submitted for FileField: %r', mode)
            return self._existing_value
        return file

    def to_python(self, value):
        value = self._to_python(**value)
        #XXX Hack
        self.field.set_raw_value(self.field.form.raw_data, 
                                 self.from_python(value))
        return value


class FileFieldSet(FieldSet):
    '''FieldSet aggregating fields required for file upload handling::
    '''

    fields = [
            FileField('file',
                  conv=convs.SimpleFile(),
                  widget=widgets.FileInput()),
            Field('mode',
                  conv=convs.EnumChoice(choices=[('existing', ''),
                                                 ('temp', ''),
                                                 ('empty', ''),
                                                 ('delete', ''),],
                                        required=True),
                  widget=widgets.HiddenInput),
            Field('temp_name',
                  conv=convs.Char(required=False),
                  widget=widgets.HiddenInput),
            Field('original_name',
                  conv=convs.Char(required=False),
                  widget=widgets.HiddenInput),
        ]

    conv = FileFieldSetConv

    def __init__(self, name, conv=FileFieldSetConv, **kwargs):
        kwargs.setdefault('fields', self.fields)
        FieldSet.__init__(self, name, conv=conv, **kwargs)

    def get_initial(self):
        # Redefine because FieldSet.get_initial returns dict by default,
        # but python value of FileFieldSet is either None, either BaseFile
        # instance.
        return None

