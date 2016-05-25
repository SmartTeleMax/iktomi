'''
Data classes representing references to files in model objects. Manager class
for common operations with files. Manager encapsulate knowledge on where and
how to store transient and persistent files.
'''

import os
import base64
import errno
import mimetypes
from shutil import copyfileobj
from ..utils import cached_property
import logging

logger = logging.getLogger(__name__)


class BaseFile(object):

    def __init__(self, root, name, manager=None):
        '''@root depends on environment of application and @name uniquely
        identifies the file.'''
        self.root = root
        self.name = name
        self.manager = manager

    @property
    def path(self):
        return os.path.join(self.root, self.name)

    @property
    def mimetype(self):
        '''Guessed mimetype'''
        return mimetypes.guess_type(self.path)[0]

    @cached_property
    def size(self):
        try:
            return os.path.getsize(self.path)
        # Return None for non-existing file.
        # There can be OSError or IOError (depending on Python version?), both
        # are derived from EnvironmentError having errno property.
        except EnvironmentError as exc:
            if exc.errno!=errno.ENOENT:
                raise # pragma: no cover

    @property
    def file_name(self):
        return os.path.split(self.name)[1]

    @property
    def ext(self):
        return os.path.splitext(self.name)[1]

    def __repr__(self):
        return '{}({!r})'.format(type(self).__name__, self.name)


class TransientFile(BaseFile):

    mode = 'transient'

    @property
    def url(self):
        return self.manager.get_transient_url(self)


class PersistentFile(BaseFile):

    mode = 'existing' # XXX rename existing to persistent everywhere

    @property
    def url(self):
        return self.manager.get_persistent_url(self)


def random_name(length=32):
    # altchars - do not use "-" and "_" in file names
    name = base64.b64encode(os.urandom(length), altchars=b"AA").rstrip(b'=')
    return name[:length].decode('utf-8')


class BaseFileManager(object):

    def __init__(self, persistent_root, persistent_url):
        self.persistent_root = persistent_root
        self.persistent_url = persistent_url

    def get_persistent(self, name, cls=PersistentFile):
        if not name or '..' in name or name[0] in '~/':
            raise ValueError('Unsecure file path')
        persistent = cls(self.persistent_root, name, self)
        return persistent

    def get_persistent_url(self, file, env=None):
        return self.persistent_url + file.name


class ReadonlyFileManager(BaseFileManager):
    pass


class FileManager(BaseFileManager):

    transient_length = 16
    persistent_length = 32

    def __init__(self, transient_root, persistent_root,
                 transient_url, persistent_url,
                 transient_length=None,
                 persistent_length=None):
        self.transient_root = transient_root
        self.persistent_root = persistent_root
        self.transient_url = transient_url
        self.persistent_url = persistent_url

        self.transient_length = transient_length or self.transient_length
        self.persistent_length = persistent_length or self.persistent_length

    def delete(self, file_obj):
        if os.path.isfile(file_obj.path):
            try:
                os.unlink(file_obj.path)
            except OSError as exc:
                msg = 'ERROR: {} while deleting file {}'.format(str(exc), file_obj.path)
                logger.error(msg)
                raise
        else:
            msg = 'file {} was not found while deleting'.format(file_obj.path)
            logger.warning(msg)

    def _copy_file(self, inp, path, length=None):
        # works for ajax file upload
        # XXX implement/debug for FieldStorage and file
        with open(path, 'wb') as fp:
            if length is None:
                copyfileobj(inp, fp)
            else:
                # copyfileobj does not work on request.input_stream
                # XXX check
                pos, bufsize = 0, 16*1024
                while pos < length:
                    bufsize = min(bufsize, length-pos)
                    data = inp.read(bufsize)
                    fp.write(data)
                    assert bufsize == len(data)
                    pos += bufsize

    def create_transient(self, input_stream, original_name, length=None):
        '''Create TransientFile and file on FS from given input stream and 
        original file name.'''
        ext = os.path.splitext(original_name)[1]
        transient = self.new_transient(ext)
        if not os.path.isdir(self.transient_root):
            os.makedirs(self.transient_root)

        self._copy_file(input_stream, transient.path, length=length)
        return transient

    def new_transient(self, ext=''):
        '''Creates empty TransientFile with random name and given extension.
        File on FS is not created'''
        name = random_name(self.transient_length) + ext
        return TransientFile(self.transient_root, name, self)

    def get_transient(self, name):
        '''Restores TransientFile object with given name.
        Should be used when form is submitted with file name and no file'''
        # security checks: basically no folders are allowed
        assert not ('/' in name or '\\' in name or name[0] in '.~')
        transient = TransientFile(self.transient_root, name, self)
        if not os.path.isfile(transient.path):
            raise OSError(errno.ENOENT, 'Transient file has been lost',
                          transient.path)
        return transient

    def store(self, transient_file, persistent_file):
        '''Makes PersistentFile from TransientFile'''
        #for i in range(5):
        #    persistent_file = PersistentFile(self.persistent_root,
        #                                     persistent_name, self)
        #    if not os.path.exists(persistent_file.path):
        #        break
        #else:
        #    raise Exception('Unable to find free file name')
        dirname = os.path.dirname(persistent_file.path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        os.rename(transient_file.path, persistent_file.path)
        return persistent_file

    def get_transient_url(self, file, env=None):
        return self.transient_url + file.name

    def new_file_name(self, name_template, inst, ext, old_name):
        assert '{random}' in name_template, \
               'Non-random name templates are not supported yet'
        for i in range(5):
            name = name_template.format(item=inst,
                    random=random_name(self.persistent_length))
            name = name + ext
            # XXX Must differ from old value[s].
            if name != old_name or not '{random}' in name_template:
                return name
        raise Exception('Unable to find new file name') # pragma: no cover, very rare case

    def create_symlink(self, source_file, target_file):
        source_path = os.path.normpath(source_file.path)
        target_path = os.path.normpath(target_file.path)
        assert target_path.startswith(self.persistent_root), \
              'Target file must be in %s folder' % self.persistent_root
        target_dir = os.path.dirname(target_path)
        source_path_rel = os.path.relpath(source_path, target_dir)
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)
        if os.path.islink(target_path):
            os.unlink(target_path)
        os.symlink(source_path_rel, target_path)

