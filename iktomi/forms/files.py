# -*- coding: utf-8 -*-
import logging
from iktomi.forms import convs, widgets, Field, FieldSet, FileField
from iktomi.utils import cached_property

logger = logging.getLogger(__name__)


class FileFieldSetConv(convs.Converter):

    error_inner = 'Error uploading file'
    error_lost = 'Transient file has been lost'
    error_hacking = 'Transient file name is not provided or is incorrect'

    def from_python(self, value):
        is_transient = value and value.mode == 'transient'
        return {'transient_name': value.name if is_transient else None,
                #'original_name': value and value.original_name,
                'original_name': value.name if is_transient else None, # XXX
                'file': value,
                'mode': value.mode if value is not None else 'empty'}

    @cached_property
    def file_manager(self):
        if hasattr(self.env, 'db') and hasattr(self.env.db, 'find_file_manager'):
            # XXX ducktyping hack?
            return self.env.db.find_file_manager(self.field.form.model)
        return self.env.file_manager

    def _to_python(self, file=None, mode=None,
                   transient_name=None, original_name=None):

        file_manager = self.file_manager

        if not self._is_empty(file):
            file = file_manager.create_transient(file.file, file.filename)
        else:
            file = None

        if mode == 'empty':
            if not file and self.required:
                raise convs.ValidationError(self.error_required)

        elif mode == 'transient':
            if not original_name:
                logger.warning('Missing original_name for FileField')
            if not transient_name:
                logger.warning('Missing transient_name for FileField '
                               'in mode "transient"')
                raise convs.ValidationError(self.error_hacking)

            try:
                transient_file = file_manager.get_transient(transient_name)
            except OSError:
                raise convs.ValidationError(self.error_lost)

            if file:
                file_manager.delete(transient_file)
            else:
                file = transient_file

        elif mode == 'existing':
            if not file:
                return self._existing_value

        return file

    def to_python(self, value):
        value = self._to_python(**value)
        #XXX Hack
        self.field.set_raw_value(self.field.form.raw_data, 
                                 self.from_python(value))
        return value


def check_file_path(conv, value):
    if value and ('/' in value or '\\' in value or value[0] in '.~'):
        logger.warning('Hacking attempt: submitted temp_name '\
                       'for FileField contains "/"')
        raise convs.ValidationError('Invalid filename')
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
                                                 ('transient', ''),
                                                 ('empty', '')],
                                        required=True),
                  widget=widgets.HiddenInput),
            Field('transient_name',
                  conv=convs.Char(check_file_path, required=False),
                  widget=widgets.HiddenInput),
            Field('original_name',
                  conv=convs.Char(check_file_path, required=False),
                  widget=widgets.HiddenInput),
        ]

    conv = FileFieldSetConv

    def __init__(self, name, **kwargs):
        kwargs.setdefault('fields', self.fields)
        kwargs.setdefault('conv', self.conv)
        FieldSet.__init__(self, name, **kwargs)

    def get_initial(self):
        # Redefine because FieldSet.get_initial returns dict by default,
        # but python value of FileFieldSet is either None, either BaseFile
        # instance.
        return None

