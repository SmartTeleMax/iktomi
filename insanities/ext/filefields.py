# -*- coding: utf-8 -*-
import cgi
from os import path
import os, struct, tempfile, time, logging

from ..utils import cached_property
from ..forms import convs, widgets
from ..forms.fields import Field, FieldSet, FileField

logger = logging.getLogger(__name__)


def time_uid():
    return (struct.pack('!d', time.time()) + os.urandom(2)).encode('hex')

def _get_file_content(f):
    if isinstance(f, cgi.FieldStorage):
        return f.value
    return f.read()


class UploadedFile(object):

    @property
    def temp_path(self):
        return tempfile.gettempdir()
    @property
    def base_path(self):
        raise NotImplementedError
    @property
    def base_temp_url(self):
        return '/form-temp/'
    @property
    def base_url(self):
        raise NotImplementedError


    def __init__(self, temp_name=None, original_name=None, saved_name=None):
        self.original_name = original_name
        self.temp_name = temp_name
        self.saved_name = saved_name
        self.uid = time_uid()

        if temp_name is not None:
            self.uid, self.ext = path.splitext(temp_name)
            self.mode = 'temp' # XXX use not-string flags
        elif saved_name is not None:
            self.mode = 'existing'
        else:
            self.mode = 'empty'

    @property
    def full_path(self):
        if self.mode == 'temp':
            return path.join(self.temp_path, self.temp_name)
        elif self.mode == 'existing':
            return path.join(self.base_path, self.saved_name)

    @property
    def url(self):
        if self.mode == 'temp':
            return self.base_temp_url + self.uid + self.ext
        elif self.mode == 'existing':
            return self.base_url + self.saved_name

    @cached_property
    def size(self):
        return os.path.getsize(self.full_path)

    def save_temp(self, file, lazy=False):
        self.ext = path.splitext(self.original_name)[1]
        self.temp_name = self.uid + self.ext
        self.mode = 'temp'
        self._input_stream = file
        if not lazy:
            self.do_save_temp()

    def do_save_temp(self):
        # finish delayed file save
        if not path.isdir(self.temp_path):
            os.makedirs(self.temp_path)
        try:
            fp = open(self.full_path, 'wb')
            fp.write(_get_file_content(self._input_stream))
            fp.close()
        except Exception, e:
            raise convs.ValidationError(u"couldn't save file: %s" % e)

    def delete(self):
        if path.isfile(self.full_path):
            try:
                os.unlink(self.full_path)
            except OSError:
                pass



def check_file_path(value):
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
            tmp = self.file_cls(original_name=file.filename)
            # file.file - due to FieldStorage interface
            tmp.save_temp(file.file)
            return tmp
        return None


class FileFieldSetConv(convs.Converter):

    hacking = u'Что-то пошло не так'
    null = True

    @property
    def file_cls(self):
        return self.field.file_cls

    def from_python(self, value):
        return {'temp_name': value and value.temp_name,
                'original_name': value and value.original_name,
                'delete': False, 'file': value,
                'mode': value.mode if value is not None else 'empty'}

    def _to_python(self, file=None, mode=None, temp_name=None, original_name=None, delete=False):
        '''
            file - UploadedFile instance
        '''
        temp_file = self.file_cls(temp_name=temp_name, original_name=original_name)

        if mode == 'empty':
            if not file and self.required:
                raise convs.ValidationError(self.error_required)

        elif mode == 'temp':
            if not original_name:
                logger.warning('Missing original_name for FileField')
            if not temp_name:
                logger.warning('Missing temp_name for FileField in mode "temp"')
                raise convs.ValidationError(self.hacking)

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

        if delete:
            return None
        return file

    def to_python(self, value):
        value = self._to_python(**value)
        #XXX Hack
        self.field.set_raw_value(self.from_python(value))
        return value


class FileFieldSet(FieldSet):
    '''
    Container field aggregating a couple of other different fields
    '''

    fields = [
        FileField('file',
                  conv=TempFileConv(file_cls=UploadedFile),
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
    file_cls = UploadedFile

    def __init__(self, name, conv=FileFieldSetConv, **kwargs):
        kwargs.setdefault('fields', self.fields)
        FieldSet.__init__(self, name, conv=conv, **kwargs)
        #self.get_field('file').conv.required = self.conv.required

    def get_initial(self):
        return None # XXX
