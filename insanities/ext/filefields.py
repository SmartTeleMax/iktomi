# -*- coding: utf-8 -*-
import cgi
import string
from os import path
import os, struct, tempfile, time
from PIL import Image

from ..utils import weakproxy, cached_property
from ..forms import convs
from ..forms.fields import Field
from ..forms.ui import widgets


def time_uid():
    return (struct.pack('!d', time.time()) + os.urandom(2)).encode('hex')

def _get_file_content(f):
    if isinstance(f, cgi.FieldStorage):
        return f.value
    return f.read()


class BaseFile(object):

    def __init__(self, base_path, name, ext):
        self.base_path = base_path
        self.name = name
        self.ext = ext


class TempUploadedFile(BaseFile):

    def __init__(self, temp_dir=None, name=None, ext=None, uid=None):
        self.temp_path = temp_dir or tempfile.gettempdir()
        super(TempUploadedFile, self).__init__(self.temp_path, name, ext)
        self.uid = uid or time_uid()

    @cached_property
    def full_path(self):
        return path.join(self.temp_path, self.uid + self.ext)

    def save(self, file):
        if not self.name or not self.ext:
            self.name, self.ext = path.splitext(file.name)
        if not path.isdir(self.temp_path):
            os.makedirs(self.temp_path)
        try:
            fp = open(self.full_path, 'wb')
            fp.write(_get_file_content(file))
            fp.close()
        except Exception, e:
            raise convs.ValidationError(u"coudn't save file: %s" % e)

    def delete(self):
        if path.isfile(self.full_path):
            try:
                os.unlink(self.full_path)
            except OSError:
                pass


class TempImageFile(TempUploadedFile):

    invalid_image = u'The file is not valid image'

    def __init__(self, field, name=None, ext=None, uid=None):
        super(TempImageFile, self).__init__(field, name=name, ext=ext, uid=uid)
        self.thumb_size = field.thumb_size
        self.thumb_sufix = field.thumb_sufix

    @cached_property
    def thumb_filename(self):
        return path.join(self.temp_path, self.uid + self.thumb_sufix + '.png')

    def save(self, file):
        try:
            image = Image.open(file)
        except IOError, e:
            raise convs.ValidationError(self.invalid_image)
        file.seek(0)
        super(TempImageFile, self).save(file)
        if self.thumb_size:
            image.thumbnail(self.thumb_size, Image.ANTIALIAS)
            image.save(self.thumb_filename, quality=85)

    def delete(self):
        super(TempImageFile, self).delete()
        if self.thumb_size:
            if path.isfile(self.thumb_filename):
                try:
                    os.unlink(self.thumb_filename)
                except OSError:
                    pass


class StoredFile(BaseFile):

    def __init__(self, filename, base_path, base_url):
        name, ext = path.splitext(filename)
        super(StoredFile, self).__init__(base_path, name, ext)
        self.filename = filename
        self.base_url = base_url

    @cached_property
    def full_path(self):
        return path.join(self.base_path, self.filename)

    @cached_property
    def size(self):
        return os.path.getsize(self.full_path)

    @cached_property
    def url(self):
        return self.base_url + self.filename


class StoredImageFile(StoredFile):

    @cached_property
    def image(self):
        return Image.open(self.full_path)


def check_file_path(value):
    if value and '/' in value:
        logger.warning('Hacking attempt: submitted temp_name '\
                       'for FileField contains "/"')
        raise ValidationError('Invalid filename')
    return value

class TempFile(convs.Converter):

    hacking = u'Что-то пошло не так'
    temp_file_cls = TempUploadedFile
    stored_file_cls = StoredFile
    null = True

    subfields = [
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
        Field('delete', conv=convs.Bool(), label='Delete'),
    ]

    @cached_property
    def temp_dir(self):
        # Can be overwritten
        return self.field.env.temp_path

    @cached_property
    def temp_url(self):
        # Can be overwritten
        return self.field.env.temp_url

    def from_python(self, value):
        data = {'temp_name': '', 'original_name': '', 'delete': False}
        if isinstance(value, self.stored_file_cls):
            data['mode'] = 'existing'
        elif isinstance(value, self.temp_file_cls):
            data['mode'] = 'temp'
            data['temp_name'] = value.uid + value.ext
            data['original_name'] = value.name
        else:
            data['mode'] = 'empty'
        return data

    def to_python(self, file, mode=None, temp_name=None, original_name=None, delete=False):

#        if file and file.filename == '<fdopen>':
#            file.filename = None

        if mode == 'empty':
            if file == u'' or file is None: #XXX WEBOB ONLY !!!
                if self.required:
                    raise convs.ValidationError(self.required)
                raise convs.SkipReadonly # XXX This is incorrect
            return self.save_temp_file(file)

        elif mode == 'temp':
            if not original_name:
                logger.warning('Missing original_name for FileField')
            if temp_name:
                if not path.isfile(path.join(self.env.temp_path, temp_name)):
                    raise convs.ValidationError(u'Временный файл утерян')
                if not (file and file.filename):
                    uid, ext = path.splitext(temp_name)
                    return self.temp_file_cls(self, original_name, ext, uid)
                self.delete_temp_file(temp_name)
                if delete:
                    return None
                return self.save_temp_file(file)
            else:
                logger.warning('Missing temp_name for FileField in mode "temp"')
                raise convs.ValidationError(self.hacking)

        elif mode == 'existing':
            if file.filename:
                return self.save_temp_file(file)
            if delete:
                return None
            raise convs.SkipReadonly

        else:
            logger.warning('Unknown mode submitted for FileField: %r', mode)
            raise convs.SkipReadonly

    def save_temp_file(self, file):
        tmp = self.temp_file_cls(self.temp_dir)
        #XXX: file.file - due to FieldStorage interface
        tmp.save(file.file)
        return tmp

    def delete_temp_file(self, temp_name):
        uid, ext = path.splitext(temp_name)
        tmp = self.temp_file_cls(self.temp_dir, name=None, ext=ext, uid=uid)
        tmp.delete()

class TempFileWidget(widgets.Widget):

    template = 'widgets/fileinput.html'

    def prepare_data(self, **kwargs):
        data = widgets.Widget.prepare_data(self, **kwargs)
        data['value'] = value = data['field'].value
        data['mode'] = value['mode']
        return data
