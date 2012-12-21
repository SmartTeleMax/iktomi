# -*- coding: utf-8 -*-

class StorageFrame(object):

    def __init__(self, _parent_storage=None, **kwargs):
        self._parent_storage = _parent_storage
        self.__dict__.update(kwargs)

    def __getattr__(self, name):
        return getattr(self._parent_storage, name)

    def as_dict(self):
        d = dict(self._parent_storage.as_dict() if self._parent_storage else {},
                 **self.__dict__)
        # XXX delete _parent_storage?
        del d['_parent_storage']
        return d

class VersionedStorage(object):

    def __init__(self, cls=StorageFrame, *args, **kwargs):
        self._storage = cls(*args, **kwargs)

    def _push(self):
        self._storage = VersionedStorage(
                    _parent_storage=self._storage)

    def _pop(self):
        self._storage = self._storage._parent_storage

    def __getattr__(self, name):
        return getattr(self._storage, name)

    def __setattr__(self, name, value):
        if name == '_storage':
            self.__dict__[name] = value
        else:
            setattr(self._storage, name, value)

    def __delattr__(self, name):
        delattr(self._storage, name)

    def as_dict(self):
        return self._storage.as_dict()
