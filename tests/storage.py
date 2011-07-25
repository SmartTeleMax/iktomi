# -*- coding: utf-8 -*-

__all__ = ['LocalMemStorageTest']

import unittest
from insanities.storage import LocalMemStorage


class LocalMemStorageTest(unittest.TestCase):
    def test_set(self):
        '`LocalMemStorage` set method'
        s = LocalMemStorage()
        s.set('key', 'value')
        self.assertEqual(s.storage['key'], 'value')

    def test_set_rewrite(self):
        '`LocalMemStorage` set method of existing key'
        s = LocalMemStorage()
        s.set('key', 'value')
        s.set('key', 'value1')
        self.assertEqual(s.storage['key'], 'value1')

    def test_get(self):
        '`LocalMemStorage` get method'
        s = LocalMemStorage()
        s.set('key', 'value')
        self.assertEqual(s.get('key'), 'value')
        self.assertEqual(s.get('key1'), None)
        self.assertEqual(s.get('key1', '1'), '1')

    def test_delete(self):
        '`LocalMemStorage` delete method'
        s = LocalMemStorage()
        s.set('key', 'value')
        self.assertEqual(s.delete('key'), True)
