'''
Data classes representing references to files in model objects. Manager class
for common operations with files. Manager encapsulate knowledge on where and
how to store transient and persistent files.
'''

import os
import cgi
import errno
from ..utils import cached_property


def _get_file_content(f):
    # XXX FieldStorage has no read()?
    if isinstance(f, cgi.FieldStorage):
        return f.value
    return f.read()


class BaseFile(object):

    def __init__(self, root, name):
        '''@root depends on environment of application and @name uniquely
        identifies the file.'''
        self.root = root
        self.name = name

    @property
    def path(self):
        os.path.join(self.root, self.name)

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
        if os.path.isfile(self.full_path):
            try:
                os.unlink(self.full_path)
            except OSError:
                pass

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.name)


class TransientFile(BaseFile):
    pass


class PersistentFile(BaseFile):
    pass


class MediaFileManager(object):

    def __init__(self, transient_root, persistent_root):
        self.transient_root = transient_root
        self.persistent_root = persistent_root

    def make_transient_from_fs(self, fs):
        '''Create TransientFile from cgi.FieldStorage'''
        return self.make_transient(fs.file, fs.filename)

    def make_transient(self, input_stream, original_name):
        '''Create TransientFile with given input stream and file name'''
        ext = os.path.splitext(original_name)[1]
        transient = self.new_transient(ext)
        if not os.path.isdir(self.transient_root):
            os.makedirs(self.base_path)

        with open(transient.path, 'wb') as fp:
            # XXX buffer?
            fp.write(self._get_file_content(input_stream))
        return transient

    def new_transient(self, ext=''):
        '''Creates empty TransientFile with random name and given extension'''
        name = os.urandom(8).encode('hex') + ext
        return TransientFile(self.transient_root, name)

    def restore_transient(self, name):
        '''Restores TransientFile object with given name.
        Should be used when form is submitted with file name and no file'''
        # security checks: basically no folders are allowed
        if '/' in name or '\\' in name:
            #logger.warning('Hacking attempt: submitted temp_name '\
            #               'for FileField contains "/"')
            raise # XXX
        transient = TransientFile(self.transient_root, name)
        if not os.path.isfile(transient.path):
            raise # XXX
        return transient

    def store(self, transient_file, persistent_name):
        '''Makes PersistentFile from TransientFile'''
        persistent_file = PersistentFile(self.persistent_root, persistent_name)
        os.rename(transient_file.path, persistent_file.path)
        return persistent_file


def filesessionmaker(sessionmaker, media_file_manager):
    u'''Wrapper of session maker adding link to a MediaFileManager instance
    to session.::
        
        media_file_manager = MediaFileManager(cfg.TRANSIENT_ROOT,
                                              cfg.PERSISTENT_ROOT)
        filesessionmaker(sessionmaker(…), media_file_manager)
    '''
    def session_maker(*args, **kwargs):
        session = sessionmaker(*args, **kwargs)
        # XXX in case we want to use session manager somehow bound 
        #     to request environment. For example, to generate user-specific
        #     URLs.
        #session.media_file_manager = \
        #        kwargs.get('media_file_manager', media_file_manager)
        session.media_file_manager = media_file_manager
        return session
    return session_maker

