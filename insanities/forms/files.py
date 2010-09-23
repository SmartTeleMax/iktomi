# -*- coding: utf-8 -*-
import cgi
import string
from os import path
import os, struct, tempfile, time
from PIL import Image
from ..utils import weakproxy, cached_property
from .fields import Field
from .ui.widgets import FileInput, ImageInput
from . import convs


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

    def __init__(self, tempdir_or_field=None, name=None, ext=None, uid=None):
        if tempdir_or_field is None:
            self.temp_path = tempfile.gettempdir()
        elif isinstance(tempdir_or_field, FileField):
            self.temp_path = tempdir_or_field.env.temp_path
        elif isinstance(tempdir_or_field, basestring):
            self.temp_path = tempdir_or_field
        else:
            raise TypeError('Bad tempdir param: %r %s; expected None, a string (path) or a FileField' % (type(tempdir_or_field), tempdir_or_field))
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


class FileField(Field):

    hacking = u'Что-то пошло не так'
    required = u'Обязательное поле'
    temp_file_cls = TempUploadedFile
    stored_file_cls = StoredFile
    null = True
    widget = FileInput

    def from_python(self, value):
        return value

    def to_python(self, value):
        return value

    def fill(self, data, value):
        if isinstance(value, self.stored_file_cls):
            data[self.input_name + '__mode'] = 'existing'
        elif isinstance(value, TempUploadedFile):
            data[self.input_name + '__mode'] = 'temp'
            data[self.input_name + '__temp_name'] = value.uid + value.ext
            data[self.input_name + '__original_name'] = value.name
        else:
            data[self.input_name + '__mode'] = 'empty'

    def accept(self):
        if 'w' not in self.permissions:
            raise convs.SkipReadonly
        mode = self.form.data.get(self.input_name + '__mode', None)
        file = self.form.files.get(self.input_name + '__file', None)
        temp_name = self.form.data.get(self.input_name + '__temp_name', None)
        original_name = self.form.data.get(self.input_name + '__original_name',
                                           None)
        delete = self.form.data.get(self.input_name + '__delete', None) 

#        if file and file.filename == '<fdopen>':
#            file.filename = None

        if mode == 'empty':
            if file == u'' or file is None: #XXX WEBOB ONLY !!!
                if not self.null:
                    raise convs.SkipReadonly # XXX this is incorrect
                raise convs.ValidationError(self.required)
            return self.save_temp_file(file)

        if mode == 'temp':

            if not original_name:
                raise convs.ValidationError(self.hacking)

            if temp_name and ('/' not in temp_name):

                if not path.isfile(path.join(self.env.temp_path, temp_name)):
                    raise convs.ValidationError(u'Временный файл утерян')

                if not (file and file.filename):
                    uid, ext = path.splitext(temp_name)
                    return self.temp_file_cls(self, original_name, ext, uid)

                self.delete_temp_file(temp_name)

                if delete:
                    return None

                return self.save_temp_file(file)

            raise convs.ValidationError(self.hacking)

        if mode == 'existing':
            if file.filename:
                return self.save_temp_file(file)
            if delete:
                return None
            raise convs.SkipReadonly

        raise convs.ValidationError(self.hacking)

    def save_temp_file(self, file):
        tmp = self.temp_file_cls(self)
        #XXX: file.file - due to FieldStorage interface
        tmp.save(file.file)
        return tmp

    def delete_temp_file(self, temp_name):
        uid, ext = path.splitext(temp_name)
        tmp = self.temp_file_cls(self, name=None, ext=ext, uid=uid)
        tmp.delete()


class ImageField(FileField):

    widget = ImageInput
    temp_file_cls = TempImageFile
    thumb_size = None
    thumb_sufix = '__thumb'
