
class StackedDict(object):
    # XXX i don't like this realization

    def __init__(self, **kwargs):
        self._current_data = data = kwargs
        self._stack = [[data, False]]
        self._changed = False

    def commit(self):
        data, changed = self._stack.pop()
        olddata, oldchanged = self._stack.pop()
        self._changed = changed or oldchanged
        self._stack.append([data, changed])

    def rollback(self):
        self._stack.pop()
        self._current_data, self._changed = self._stack[-1]

    def lazy_copy(self):
        self._stack.append([self._current_data, False])
        self._changed = False

    def _do_copy(self):
        self._current_data = self._current_data.copy()
        self._stack[-1][0] = self._current_data
        self._stack[-1][1] = self._changed = True

    def __setitem__(self, k, v):
        if not self._changed:
            self._do_copy()
        self._current_data[k] = v

    def __contains__(self, k):
        return k in self._current_data

    def __getitem__(self, k):
        return self._current_data[k]

    def __delitem__(self, k):
        if not self._changed:
            self._do_copy()
        del self._current_data[k]

    def update(self, other):
        if not self._changed:
            self._do_copy()
        self._current_data.update(other)

    def __getattr__(self, name):
        if name in self._current_data:
            return self._current_data[name]
        raise AttributeError(name)

    def get(self, name, default=None):
        return self._current_data.get(name, default)

    def as_dict(self):
        return self._current_data.copy()

    def __repr__(self):
        return repr(self._current_data)


