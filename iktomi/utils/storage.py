# -*- coding: utf-8 -*-
'''
Versioned storage, a classes for `env` and `data` objects.
'''

class StorageFrame(object):

    '''A single frame in the storage'''

    def __init__(self, _parent_storage=None, **kwargs):
        self._parent_storage = _parent_storage
        self.__dict__.update(kwargs)

    def as_dict(self):
        d = dict(self._parent_storage.as_dict() if self._parent_storage else {},
                 **self.__dict__)
        # XXX delete _parent_storage?
        del d['_parent_storage']
        if '_root_storage' in d:
            del d['_root_storage']
        return d

class VersionedStorage(object):
    '''Storage implements state managing interface, allowing to safely set
    attributes for `env` and `data` objects.

    Safity means that state of the storage is rolled back every time routing
    case returns ContinueRoute signal (`None`).

    Be very accurate defining methods or properties for storage, choose correct
    method or property type depending on what do you want to achieve.

    Regular methods will hold the state of storage frame they are added to.
    If you want to have an access to actual value, use storage property and
    method decorators.'''

    def __init__(self, cls=StorageFrame, *args, **kwargs):
        kwargs['_root_storage'] = self
        self._storage = cls(*args, **kwargs)

    def _push(self, **kwargs):
        self._storage = StorageFrame(_parent_storage=self._storage, **kwargs)
        return self._storage

    def _pop(self):
        self._storage = self._storage._parent_storage

    def __getattr__(self, name):
        frame = self._storage
        while frame:
            try:
                return getattr(frame, name)
            except AttributeError:
                frame = frame._parent_storage
        #raise AttributeError(name)
        raise AttributeError("{} has no attribute {}".format(
                             self.__class__.__name__, name))

    def __setattr__(self, name, value):
        if name == '_storage':
            self.__dict__[name] = value
        else:
            setattr(self._storage, name, value)

    def __delattr__(self, name):
        delattr(self._storage, name)

    def as_dict(self):
        '''Returns attributes of storage as dict'''
        return self._storage.as_dict()


class storage_property_base(object):

    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__
        self.__doc__ = method.__doc__


class storage_property(storage_property_base):
    '''Turns decorated method into storage property (method is called with
       VersionedStorage as self).'''

    def __get__(self, inst, cls):
        if inst is None:
            return self
        return self.method(inst._root_storage)


class storage_cached_property(storage_property_base):
    '''Turns decorated method into storage cached property 
       (method is called only once with VersionedStorage as self).'''

    def __get__(self, inst, cls):
        if inst is None:
            return self
        result = self.method(inst._root_storage)
        setattr(inst, self.name, result)
        return result

def storage_method(func):
    '''Calls decorated method with VersionedStorage as self'''
    def wrap(self, *args, **kwargs):
        return func(self._root_storage, *args, **kwargs)
    return wrap
