# -*- coding: utf-8 -*-
import cgi
from os import path
import os, struct, tempfile, time, logging

from ..utils import cached_property
from ..forms import convs, widgets
from ..forms.fields import Field, FieldSet, FileField
import errno

logger = logging.getLogger(__name__)


def time_uid():
    return (struct.pack('!d', time.time()) + os.urandom(2)).encode('hex')

def _get_file_content(f):
    if isinstance(f, cgi.FieldStorage):
        return f.value
    return f.read()


class UploadedFile(object):

    def __init__(self, filename=None, original_name=None, base_path=None, base_url=None):
        self.filename = filename
        self.original_name = original_name
        self.base_url = base_url
        self.base_path = base_path

    @property
    def full_path(self):
        return path.join(self.base_path, self.filename)

    @property
    def url(self):
        return self.base_url + self.filename

    @cached_property
    def size(self):
        try:
            return os.path.getsize(self.full_path)
        # Return None for non-existing file.
        # There can be OSError or IOError (depending on Python version?), both
        # are derived from EnvironmentError having errno property.
        except EnvironmentError, exc:
            if exc.errno!=errno.ENOENT:
                raise

    def delete(self):
        if path.isfile(self.full_path):
            try:
                os.unlink(self.full_path)
            except OSError:
                pass


class TempUploadedFile(UploadedFile):

    mode = 'temp'

    def __init__(self, filename=None, original_name=None,
                 base_path=None, base_url=None,
                 form_field=None):

        self.form_field = form_field
        if form_field:
            base_url = form_field.base_temp_path
            base_path = form_field.base_temp_url
        base_path = base_path or tempfile.gettempdir()
        base_url = base_url or '/form-temp/'

        UploadedFile.__init__(self, filename, original_name=original_name,
                              base_path=base_path, base_url=base_url)
        if self.filename is None and self.original_name is not None:
            self.uid = time_uid()
            self.ext = path.splitext(self.original_name)[1]
            self.filename = self.uid + self.ext
        else:
            self.uid, self.ext = path.splitext(self.filename)

    def save(self, input_file, lazy=False):
        self.ext = path.splitext(self.original_name)[1]
        self.temp_name = self.uid + self.ext
        self.mode = 'temp'
        self._input_stream = input_file
        if not lazy:
            self.do_save_temp()

    def do_save_temp(self):
        # finish delayed file save
        if not path.isdir(self.base_path):
            os.makedirs(self.base_path)
        try:
            fp = open(self.full_path, 'wb')
            fp.write(_get_file_content(self._input_stream))
            fp.close()
        except Exception, e:
            # XXX
            raise convs.ValidationError(u"couldn't save file: %s" % e)

    def delete(self):
        if path.isfile(self.full_path):
            try:
                os.unlink(self.full_path)
            except OSError:
                pass


class StoredFile(UploadedFile):

    mode = 'existing'


def check_file_path(conv, value):
    if value and '/' in value:
        logger.warning('Hacking attempt: submitted temp_name '\
                       'for FileField contains "/"')
        raise convs.ValidationError('Invalid filename')
    return value


class TempFileConv(convs.SimpleFile):

    @property
    def file_cls(self):
        return self.field.parent.file_cls

    def to_python(self, file):
        if not self._is_empty(file):
            tmp = self.file_cls(original_name=file.filename,
                                form_field=self.field,
                                base_path=self.field.base_temp_path,
                                base_url=self.field.base_temp_url)
            # file.file - due to FieldStorage interface
            tmp.save(file.file)
            return tmp
        return None


class FileFieldSetConv(convs.Converter):

    hacking = u'Что-то пошло не так'
    null = True

    @property
    def file_cls(self):
        return self.field.file_cls

    def from_python(self, value):
        return {'temp_name': value.filename if value and value.mode == 'temp' else None,
                'original_name': value and value.original_name,
                'delete': False,
                'file': value,
                'mode': value.mode if value is not None else 'empty'}

    def _to_python(self, file=None, mode=None, temp_name=None, original_name=None, delete=False):
        '''
            file - UploadedFile instance
        '''

        if delete:
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

            temp_file = self.file_cls(filename=temp_name,
                                      original_name=original_name,
                                      form_field=self.field)
            if file:
                temp_file.delete()
            else:
                if not path.isfile(temp_file.full_path):
                    raise convs.ValidationError(u'Временный файл утерян')
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


class FileFieldInFieldSet(FileField):

    @property
    def base_temp_url(self):
        return self.parent.base_temp_url
    @property
    def base_temp_path(self):
        return self.parent.base_temp_path
    @property
    def file_cls(self):
        return self.parent.file_cls


class FileFieldSet(FieldSet):
    '''
    Container field aggregating a couple of other different fields
    '''

    base_temp_url = None
    base_temp_path = None

    fields = [
            FileFieldInFieldSet('file',
                  conv=TempFileConv(),
                  widget=widgets.FileInput()),
            Field('mode',
                  conv=convs.EnumChoice(choices=[('existing', ''),
                                                 ('temp', ''),
                                                 ('empty', ''),],
                                        required=True),
                  widget=widgets.HiddenInput),
            Field('temp_name',
                  conv=convs.Char(check_file_path, required=False),
                  widget=widgets.HiddenInput),
            Field('original_name',
                  conv=convs.Char(required=False),
                  widget=widgets.HiddenInput),
            Field('delete', conv=convs.Bool(), label='Delete',
                  widget=widgets.CheckBox),
        ]

    conv = FileFieldSetConv
    file_cls = TempUploadedFile

    def __init__(self, name, conv=FileFieldSetConv, **kwargs):
        kwargs.setdefault('fields', self.fields)
        FieldSet.__init__(self, name, conv=conv, **kwargs)
        #self.get_field('file').conv.required = self.conv.required

    def get_initial(self):
        return None # XXX
