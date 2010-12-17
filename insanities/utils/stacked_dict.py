# -*- coding: utf-8 -*-

class StackedDict(object):
    def __init__(self, *args, **kwargs):
        self._stack = [{}]
        self._current_data = dict(*args, **kwargs)

    @property
    def something_new(self):
        return self._stack[-1] != self._current_data

    def commit(self):
        if self.something_new:
            self._stack.append(self._current_data.copy())

    def rollback(self):
        if len(self._stack) > 1:
            self._current_data = self._stack.pop()

    def as_dict(self):
        return self._current_data.copy()

    def __setitem__(self, k, v):
        self._current_data[k] = v

    def __getitem__(self, k):
        return self._current_data[k]

    def __delitem__(self, k):
        del self._current_data[k]

    def __getattr__(self, k):
        if k in self._current_data:
            return self._current_data[k]
        raise AttributeError(k)

    def __delattr__(self, k):
        del self._current_data[k]
