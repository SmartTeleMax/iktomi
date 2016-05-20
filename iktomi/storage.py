# -*- coding: utf-8 -*-


class Storage(object):
    def set(self, key, value, time=0):# pragma: no cover
        raise NotImplementedError()
    def get(self, key, default=None):# pragma: no cover
        raise NotImplementedError()
    def delete(self, key):# pragma: no cover
        raise NotImplementedError()


class LocalMemStorage(Storage):
    def __init__(self):
        self.storage = {}

    def set(self, key, value, time=0):
        self.storage[key] = value
        return True

    def get(self, key, default=None):
        return self.storage.get(key, default)

    def delete(self, key):
        if key in self.storage:
            del self.storage[key]
        return True


class MemcachedStorage(Storage):
    def __init__(self, conf):
        import memcache
        conf = conf if isinstance(conf, (list, tuple)) else [conf]
        self.storage = memcache.Client(conf)

    def set(self, key, value, time=0):
        return self.storage.set(key, value, time)

    def get(self, key, default=None):
        value = self.storage.get(key)
        if value is None:
            return default
        return value

    def delete(self, key):
        return self.storage.delete(key)
