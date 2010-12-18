# -*- coding: utf-8 -*-

__all__ = ['StackedDictTests']

import unittest
from insanities.utils.stacked_dict import StackedDict


class StackedDictTests(unittest.TestCase):

    def test_property(self):
        'StackedDict something_new property'
        d = StackedDict()
        self.assert_(not d._something_new)
        d['c'] = 2
        self.assert_(d._something_new)
        del d['c']
        self.assert_(not d._something_new)

    def test_init_with_initial(self):
        'StackedDict initialization with initial data'
        d = StackedDict(a=1, b=2)
        self.assert_(d._something_new)
        d['c'] = 2
        self.assert_(d._something_new)
        del d['c']
        del d['a']
        del d['b']
        self.assert_(not d._something_new)

    def test_commit(self):
        'StackedDict "commit" method'
        d = StackedDict()
        d['a'] = 1
        d._commit()
        self.assert_(not d._something_new)
        self.assertEqual(d._StackedDict__stack, [{}, {'a': 1}], 'Incorrect stack state')
        self.assertEqual(d['a'] , 1)
        self.assertRaises(KeyError, lambda: d['b'])

        # second commit do nothing
        d._commit()
        self.assert_(not d._something_new)
        self.assertEqual(d._StackedDict__stack, [{}, {'a': 1}])
        self.assertEqual(d.as_dict(), {'a': 1})
        self.assertRaises(KeyError, lambda: d['b'])

    def test_rollback_empty(self):
        'StackedDict "rollback" method on empty dict'
        d = StackedDict()
        d._rollback()
        self.assertEqual(d._StackedDict__stack, [{}])
        self.assert_(not d._something_new)

    def test_rollback(self):
        'StackedDict "rollback" method'
        d = StackedDict()
        d['a'] = 1
        d._commit()
        d['b'] = 2
        self.assertEqual(d.as_dict(), {'a': 1, 'b': 2})
        d._rollback()
        self.assertEqual(d.as_dict(), {'a': 1})
        self.assertEqual(d._StackedDict__stack, [{}])

    def test_getattr(self):
        'StackedDict getattr method'
        d = StackedDict(b=2)
        d['a'] = 1
        self.assertEqual(d.as_dict(), {'a': 1, 'b': 2})
        self.assertEqual(d.a, 1)
        self.assertEqual(d.b, 2)

    def test_setattr(self):
        'StackedDict __setattr__ method'
        d = StackedDict()
        d.c = 3
        self.assertEqual(d.c, 3)
        self.assert_(d._something_new)

    def test_delattr(self):
        'StackedDict __delattr__ method'
        d = StackedDict(a=1)
        self.assertEqual(d.a, 1)
        del d.a
        self.assertEqual(d.as_dict(), {})

    def test_contains(self):
        'StackedDict __contains__ method'
        d = StackedDict(a=1)
        d.b = 2
        d['c'] = 3
        self.assert_('a' in d)
        self.assert_('b' in d)
        self.assert_('c' in d)
