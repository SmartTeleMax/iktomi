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
            def var(self):
                return self.value + 3

            @storage_property
            def var1(self):
                return self.value + 5

            @storage_method
            def var2(self):
                return self.value + 7

        vs = VersionedStorage(Env)
        vs._push(value=4)
        self.assertEqual(vs.var, 7)
        self.assertEqual(vs.var1, 9)
        self.assertEqual(vs.var2(), 11)

        vs._push(value=1)
        self.assertEqual(vs.var, 7)
        self.assertEqual(vs.var1, 6)
        self.assertEqual(vs.var2(), 8)

        vs._pop()
        vs._pop()
        self.assertEqual(vs.var, 7)
        self.assertRaises(AttributeError, lambda: vs.var1)
        self.assertRaises(AttributeError, vs.var2)

