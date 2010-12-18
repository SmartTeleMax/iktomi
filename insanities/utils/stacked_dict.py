# -*- coding: utf-8 -*-

class StackedDict(object):
    def __init__(self, *args, **kwargs):
        self.__stack = [{}]
        self.__dict__.update(dict(*args, **kwargs))

    def _get_dict(self):
        d = self.__dict__.copy()
        del d['_StackedDict__stack']
        return d

    def _set_dict(self, value):
        value['_StackedDict__stack'] = self.__stack
        self.__dict__ = value

    _dict_ = property(_get_dict, _set_dict)

    @property
    def something_new(self):
        return self.__stack[-1] != self._dict_

    def commit(self):
        if self.something_new:
            self.__stack.append(self._dict_)

    def rollback(self):
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
