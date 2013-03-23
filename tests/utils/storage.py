# -*- coding: utf-8 -*-

__all__ = ['VersionedStorageTests']

import unittest
from iktomi.utils.storage import VersionedStorage, StorageFrame, \
        storage_property, storage_cached_property, storage_method


class VersionedStorageTests(unittest.TestCase):

    def test_hasattr(self):
        'VersionedStorage __getattr__ method'
        vs = VersionedStorage(a=1)
        vs._push(b=2)
        vs._push(c=3, b=4)

        self.assert_(hasattr(vs, 'a'))
        self.assert_(hasattr(vs, 'b'))
        self.assert_(hasattr(vs, 'c'))
        self.assert_(not hasattr(vs, 'd'))

    def test_as_dict(self):
        'VersionedStorage as_dict method'
        vs = VersionedStorage(a=1)
        a = vs._storage
        b = vs._push(b=2)
        c = vs._push(c=3, b=4)

        self.assertEqual(a.as_dict(), {'a': 1})
        self.assertEqual(b.as_dict(), {'a': 1, 'b': 2})
        self.assertEqual(c.as_dict(), {'a': 1, 'b': 4, 'c': 3})

    def test_push_pop(self):
        'VersionedStorage push/pop'
        vs = VersionedStorage(a=1)
        self.assertEqual(vs.as_dict(), {'a': 1})

        vs._push(b=2)
        self.assertEqual(vs.as_dict(), {'a': 1, 'b': 2})

        vs._push(c=3, b=4)
        self.assertEqual(vs.as_dict(), {'a': 1, 'b': 4, 'c': 3})

        vs._pop()
        self.assertEqual(vs.as_dict(), {'a': 1, 'b': 2})

        vs._pop()
        self.assertEqual(vs.as_dict(), {'a': 1})

    def test_storage_properties(self):
        class Env(StorageFrame):

            @storage_cached_property
            def storage_cached(self):
                return self.value

            @storage_property
            def storage(self):
                return self.value

            @storage_method
            def method(self):
                return self.value

        vs = VersionedStorage(Env)
        vs._push(value=4)
        self.assertEqual(vs.storage_cached, 4)
        self.assertEqual(vs.storage, 4)
        self.assertEqual(vs.method(), 4)

        vs._push(value=1)
        self.assertEqual(vs.storage_cached, 4)
        self.assertEqual(vs.storage, 1)
        self.assertEqual(vs.method(), 1)

        vs._pop()
        vs._pop()
        self.assertEqual(vs.storage_cached, 4)
        self.assertRaises(AttributeError, lambda: vs.storage)
        self.assertRaises(AttributeError, vs.method)

