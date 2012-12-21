# -*- coding: utf-8 -*-

__all__ = ['VersionedStorageTests']

import unittest
from iktomi.utils.storage import VersionedStorage


class VersionedStorageTests(unittest.TestCase):

    def test_hasattr(self):
        'VersionedStorage __contains__ method'
        a = VersionedStorage(a=1)
        b = VersionedStorage(_parent_storage=a, b=2)
        c = VersionedStorage(_parent_storage=b, c=3, b=4)

        self.assert_(hasattr(c, 'a'))
        self.assert_(hasattr(c, 'b'))
        self.assert_(hasattr(c, 'c'))
        self.assert_(not hasattr(c, 'd'))

    def test_as_dict(self):
        'VersionedStorage __contains__ method'
        a = VersionedStorage(a=1)
        b = VersionedStorage(_parent_storage=a, b=2)
        c = VersionedStorage(_parent_storage=b, c=3, b=4)

        self.assertEqual(a.as_dict(), {'a': 1})
        self.assertEqual(b.as_dict(), {'a': 1, 'b': 2})
        self.assertEqual(c.as_dict(), {'a': 1, 'b': 4, 'c': 3})
