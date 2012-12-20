# -*- coding: utf-8 -*-

class VersionedStorage(object):
    # XXX implement on the base of dict?
    def __init__(self, _parent_storage=None, **kwargs):
        self._parent_storage = _parent_storage
        self.__dict__.update(kwargs)

    def __getattr__(self, name):
        return getattr(self._parent_storage, name)

    def __contains__(self, name):
        # XXX
        return hasattr(self, name) or (self._parent_storage and 
                                       name in self._parent_storage)

    def __getitem__(self, name):
        # XXX
        return getattr(self, name)

    def __setitem__(self, name, value):
        setattr(self, name, value)

    def as_dict(self):
        d = dict(self._parent_storage.as_dict() if self._parent_storage else {},
                 **self.__dict__)
        # XXX delete _parent_storage?
        del d['_parent_storage']
        return d

