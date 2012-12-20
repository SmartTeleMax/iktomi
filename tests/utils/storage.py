# -*- coding: utf-8 -*-

__all__ = ['VersionedStorageTests']

import unittest
from iktomi.utils.storage import VersionedStorage


class VersionedStorageTests(unittest.TestCase):

    def test_contains(self):
        'VersionedStorage __contains__ method'
        a = VersionedStorage(a=1)
        b = VersionedStorage(_parent_storage=a, b=2)
        c = VersionedStorage(_parent_storage=b, c=3, b=4)

        self.assert_('a' in c)
        self.assert_('b' in c)
        self.assert_('c' in c)
        self.assert_('d' not in c)

    def test_as_dict(self):
        'VersionedStorage __contains__ method'
        a = VersionedStorage(a=1)
        b = VersionedStorage(_parent_storage=a, b=2)
        c = VersionedStorage(_parent_storage=b, c=3, b=4)

        self.assertEqual(a.as_dict(), {'a': 1})
        self.assertEqual(b.as_dict(), {'a': 1, 'b': 2})
        self.assertEqual(c.as_dict(), {'a': 1, 'b': 4, 'c': 3})
