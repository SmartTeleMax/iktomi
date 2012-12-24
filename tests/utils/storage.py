# -*- coding: utf-8 -*-

__all__ = ['VersionedStorageTests']

import unittest
from iktomi.utils.storage import VersionedStorage, StorageFrame


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
        from iktomi.utils import cached_property

        class Env(StorageFrame):

            @cached_property
            def var(self):
                return self.value + 3

            def var2(self):
                return self.value + 5
        
        vs = VersionedStorage(Env)
        vs._push(value=4)
        self.assertEqual(vs.var, 7)
        self.assertEqual(vs.var2(), 9)
