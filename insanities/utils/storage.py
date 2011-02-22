# -*- coding: utf-8 -*-

class VersionedStorage(object):
    def __init__(self, *args, **kwargs):
        self.__stack = [{}]
        self.__dict__.update(dict(*args, **kwargs))

    def _get_dict(self):
        d = self.__dict__.copy()
        del d['_VersionedStorage__stack']
        return d

    def _set_dict(self, value):
        value['_VersionedStorage__stack'] = self.__stack
        self.__dict__ = value

    _dict_ = property(_get_dict, _set_dict)

    @property
    def _modified(self):
        return self.__stack[-1] != self._dict_

    def _commit(self):
        if self._modified:
            self.__stack.append(self._dict_)

    def _rollback(self):
        if len(self.__stack) > 1:
            self._dict_ = self.__stack.pop()

    def as_dict(self):
        return self._dict_

    def __getitem__(self, k):
        return self.__dict__[k]

    def __delitem__(self, k):
        del self.__dict__[k]

    __setitem__ = object.__setattr__

    def __contains__(self, k):
        return k in self._dict_

    def __repr__(self):
        return repr(self._dict_)

    def __call__(self, **kwargs):
        self.__dict__.update(**kwargs)
        return self
