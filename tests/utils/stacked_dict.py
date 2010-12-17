# -*- coding: utf-8 -*-

__all__ = ['StackedDictTests']

import unittest
from insanities.utils.stacked_dict import StackedDict


class StackedDictTests(unittest.TestCase):

    def test_property(self):
        'StackedDict something_new property'
        d = StackedDict()
        self.assert_(not d.something_new)
        d[1] = 2
        self.assert_(d.something_new)
        del d[1]
        self.assert_(not d.something_new)

    def test_init_with_initial(self):
        'StackedDict initialization with initial data'
        d = StackedDict(a=1, b=2)
        self.assert_(d.something_new)
        d[1] = 2
        self.assert_(d.something_new)
        del d[1]
        del d['a']
        del d['b']
        self.assert_(not d.something_new)

    def test_commit(self):
        'StackedDict "commit" method'
        d = StackedDict()
        d['a'] = 1
        d.commit()
        self.assert_(not d.something_new)
        self.assertEqual(d._stack, [{}, {'a': 1}], 'Incorrect stack state')
        self.assertEqual(d['a'] , 1)
        self.assertRaises(KeyError, lambda: d['b'])

        # second commit do nothing
        d.commit()
        self.assert_(not d.something_new)
        self.assertEqual(d._stack, [{}, {'a': 1}])
        self.assertEqual(d.as_dict(), {'a': 1})
        self.assertRaises(KeyError, lambda: d['b'])

    def test_rollback_empty(self):
        'StackedDict "rollback" method on empty dict'
        d = StackedDict()
        d.rollback()
        self.assertEqual(d._stack, [{}])
        self.assert_(not d.something_new)

    def test_rollback(self):
        'StackedDict "rollback" method'
        d = StackedDict()
        d['a'] = 1
        d.commit()
        d['b'] = 2
        self.assertEqual(d.as_dict(), {'a': 1, 'b': 2})
        d.rollback()
        self.assertEqual(d.as_dict(), {'a': 1})
        self.assertEqual(d._stack, [{}])

    def test_getattr(self):
        'StackedDict getattr method'
        d = StackedDict()
        d['a'] = 1
        self.assertEqual(d.as_dict(), {'a': 1})
