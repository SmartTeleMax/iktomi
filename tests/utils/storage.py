# -*- coding: utf-8 -*-

__all__ = ['VersionedStorageTests']

import unittest
from iktomi.utils.storage import VersionedStorage


class VersionedStorageTests(unittest.TestCase):

    #def test_property(self):
    #    'VersionedStorage something_new property'
    #    d = VersionedStorage()
    #    self.assert_(not d._modified)
    #    d['c'] = 2
    #    self.assert_(d._modified)
    #    del d['c']
    #    self.assert_(not d._modified)

    #def test_init_with_initial(self):
    #    'VersionedStorage initialization with initial data'
    #    d = VersionedStorage(a=1, b=2)
    #    self.assert_(d._modified)
    #    d['c'] = 2
    #    self.assert_(d._modified)
    #    del d['c']
    #    del d['a']
    #    del d['b']
    #    self.assert_(not d._modified)

    #def test_commit(self):
    #    'VersionedStorage "commit" method'
    #    d = VersionedStorage()
    #    d['a'] = 1
    #    d._commit()
    #    self.assert_(not d._modified)
    #    self.assertEqual(d._VersionedStorage__stack, [{}, {'a': 1}], 'Incorrect stack state')
    #    self.assertEqual(d['a'] , 1)
    #    self.assertRaises(KeyError, lambda: d['b'])

    #    # second commit do nothing
    #    d._commit()
    #    self.assert_(not d._modified)
    #    self.assertEqual(d._VersionedStorage__stack, [{}, {'a': 1}])
    #    self.assertEqual(d.as_dict(), {'a': 1})
    #    self.assertRaises(KeyError, lambda: d['b'])

    #def test_rollback_empty(self):
    #    'VersionedStorage "rollback" method on empty dict'
    #    d = VersionedStorage()
    #    d._rollback()
    #    self.assertEqual(d._VersionedStorage__stack, [{}])
    #    self.assert_(not d._modified)

    #def test_rollback(self):
    #    'VersionedStorage "rollback" method'
    #    d = VersionedStorage()
    #    d['a'] = 1
    #    d._commit()
    #    d['b'] = 2
    #    self.assertEqual(d.as_dict(), {'a': 1, 'b': 2})
    #    d._rollback()
    #    self.assertEqual(d.as_dict(), {'a': 1})
    #    self.assertEqual(d._VersionedStorage__stack, [{}])

    #def test_getattr(self):
    #    'VersionedStorage getattr method'
    #    d = VersionedStorage(b=2)
    #    d['a'] = 1
    #    self.assertEqual(d.as_dict(), {'a': 1, 'b': 2})
    #    self.assertEqual(d.a, 1)
    #    self.assertEqual(d.b, 2)

    #def test_setattr(self):
    #    'VersionedStorage __setattr__ method'
    #    d = VersionedStorage()
    #    d.c = 3
    #    self.assertEqual(d.c, 3)
    #    self.assert_(d._modified)

    #def test_delattr(self):
    #    'VersionedStorage __delattr__ method'
    #    d = VersionedStorage(a=1)
    #    self.assertEqual(d.a, 1)
    #    del d.a
    #    self.assertEqual(d.as_dict(), {})

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
