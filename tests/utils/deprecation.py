# -*- coding: utf-8 -*-

import unittest
import warnings
from iktomi.utils.deprecation import deprecated


__all__ = ['DeprecationTests']


class DeprecationTests(unittest.TestCase):

    def setUp(self):
        self.old_filters = warnings.filters[:]
        warnings.simplefilter('always')

    def tearDown(self):
        warnings.filters[:] = self.old_filters

    def test_deprecated_simple(self):
        @deprecated()
        def f(arg):
            return arg
        ARG = object()
        with warnings.catch_warnings(record=True) as recorded:
            returned = f(ARG)
        self.assertIs(returned, ARG)
        self.assertEqual(len(recorded), 1)

    def test_deprecated_comment(self):
        COMMENT = 'Never never use it!'
        @deprecated(comment=COMMENT)
        def f(arg):
            return arg
        ARG = object()
        with warnings.catch_warnings(record=True) as recorded:
            returned = f(ARG)
        self.assertIs(returned, ARG)
        self.assertEqual(len(recorded), 1)
        self.assertIn(COMMENT, str(recorded[-1].message))
