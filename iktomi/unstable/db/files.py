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
