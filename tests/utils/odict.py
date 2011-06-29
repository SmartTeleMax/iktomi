# -*- coding: utf-8 -*-

import unittest
from insanities.utils.odict import OrderedDict


class OrderedDictTests(unittest.TestCase):

    def test_pop_with_default(self):
        d = OrderedDict([('a', 'a'), ('b', 'b')])
        self.assertEqual(d.pop('a', 'c'), 'a')
        self.assertEqual(len(d.items()), 1)

    def test_pop_without_default(self):
        d = OrderedDict([('a', 'a'), ('b', 'b')])
        self.assertEqual(d.pop('a'), 'a')
        self.assertEqual(len(d.items()), 1)
