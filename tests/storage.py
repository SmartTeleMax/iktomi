# -*- coding: utf-8 -*-

__all__ = ['LocalMemStorageTest', 'MemcachedStorageTest']

import unittest
from iktomi.storage import LocalMemStorage, MemcachedStorage


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
        self.assertEqual(s.get('key'), None)
        self.assertEqual(s.get('key', '1'), '1')
        s.set('key', 'value')
        self.assertEqual(s.get('key'), 'value')

    def test_delete(self):
        '`LocalMemStorage` delete method'
        s = LocalMemStorage()
        self.assertEqual(s.delete('key'), True)
        s.set('key', 'value')
        self.assertEqual(s.delete('key'), True)
        self.assertEqual(s.get('key'), None)


class MemcachedStorageTest(unittest.TestCase):
    def setUp(self):
        self.storage = MemcachedStorage('localhost:11211')
        if not self.storage.storage.set('test', 'test'):
            raise Exception('memcached is down')

    def tearDown(self):
        memcached = self.storage.storage
        memcached.delete('test')
        memcached.delete('key')
        memcached.disconnect_all()

    def test_set(self):
        '`MemcachedStorage` set method'
        self.assertEqual(self.storage.set('key', 'value'), True)
        self.assertEqual(self.storage.set('key', 'value1'), True)

    def test_get(self):
        '`MemcachedStorage` get method'
        self.assertEqual(self.storage.get('key'), None)
        self.assertEqual(self.storage.get('key', 'default'), 'default')
        self.storage.set('key', 'value')
        self.assertEqual(self.storage.get('key'), 'value')

    def test_delete(self):
        '`MemcachedStorage` delete method'
        self.assertEqual(self.storage.delete('key'), True)
        self.storage.set('key', 'value')
        self.assertEqual(self.storage.delete('key'), True)
        self.assertEqual(self.storage.get('key'), None)
