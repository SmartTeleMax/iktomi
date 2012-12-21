# -*- coding: utf-8 -*-

class VersionedStorage(object):

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

