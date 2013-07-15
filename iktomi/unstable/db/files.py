'''
Data classes representing references to files in model objects. Manager class
for common operations with files. Manager encapsulate knowledge on where and
how to store transient and persistent files.
'''

import os


class BaseFile(object):

    def __init__(self, root, name):
        '''@root depends on environment of application and @name uniquely
        identifies the file.'''
        self.root = root
        self.name = name

    @property
    def path(self):
        os.path.join(self.root, self.name)

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

    def new_transient(self, ext=''):
        name = os.urandom(8).encode('hex') + ext
        return TransientFile(self.transient_root, name)

    def store(self, transient_file, persistent_name):
        persistent_file = PersistentFile(self.persistent_root, persistent_name)
        os.rename(transient_file.path, persistent_file.path)
        return persistent_file
