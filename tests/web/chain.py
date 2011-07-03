# -*- coding: utf-8 -*-

__all__ = ['Chain']

import unittest
from insanities import web
from insanities.web.core import _FunctionWrapper
from insanities.utils.storage import VersionedStorage


class Chain(unittest.TestCase):

    def test_functions_chain(self):
        '''Functions as a chain of handlers'''

        def handler1(env, data, nh):
            return nh(env, data)

        def handler2(env, data, nh):
            return nh(env, data)

        def handler3(env, data, nh):
            return nh(env, data)

        chain = web.handler(handler1) | handler2 | handler3

        handler = chain._next_handler
        self.assert_(isinstance(handler, _FunctionWrapper))
        self.assertEqual(handler.handle, handler2)

        handler = chain._next_handler._next_handler
        self.assert_(isinstance(handler, _FunctionWrapper))
        self.assertEqual(handler.handle, handler3)

    def test_functions_chain_call(self):
        'Functions chain call'

        def handler1(env, data, nh):
            return nh(env, data)

        def handler2(env, data, nh):
            return nh(env, data)

        chain = web.handler(handler1) | handler2

        self.assert_(chain(VersionedStorage(), VersionedStorage()) is None)

    def test_List(self):
        'cases handle'
        def h1(env, data, nh):
            self.assertEqual(env.count, 0)
            env['count'] = env['count'] + 1
            return nh(env, data)

        def h2(env, data, nh):
            self.assertEqual(env.count, 0)
            env['count'] = env['count'] + 1
            return nh(env, data)

        def h3(env, data, nh):
            self.assertEqual(env.count, 0)
            env['count'] = env['count'] + 1
            return nh(env, data)

        chain = web.cases(h1, h2, h3)
        count = VersionedStorage(count=0)
        self.assert_(chain(count, VersionedStorage()) is None)
        self.assertEqual(count['count'], 0)

    def test_list_of_chains(self):
        'cases of chains'
        def h1(env, data, nh):
            self.assertEqual(env.count, 0)
            env['count'] = env['count'] + 1
            return nh(env, data)

        def h2(env, data, nh):
            self.assertEqual(env.count, 0)
            env['count'] = env['count'] + 1
            return nh(env, data)

        def h3(env, data, nh):
            self.assertEqual(env.count, 1)
            env['count'] = env['count'] + 1
            return nh(env, data)

        chain = web.cases(h1, web.handler(h2) | h3)
        count = VersionedStorage(count=0)
        self.assert_(chain(count, VersionedStorage()) is None)
        self.assertEqual(count['count'], 0)

    def test_chain_with_list(self):
        'Chain with cases'
        def h(env, data, nh):
            self.assertEqual(env.count, 0)
            env['count'] = env['count'] + 1
            return nh(env, data)

        def h1(env, data, nh):
            self.assertEqual(env.count, 1)
            env['count'] = env['count'] + 1
            return nh(env, data)

        def h2(env, data, nh):
            self.assertEqual(env.count, 2)
            env['count'] = env['count'] + 1
            return nh(env, data)

        chain = web.handler(h) | web.cases(h1, web.handler(h1) | h2)
        count = VersionedStorage(count=0)
        self.assert_(chain(count, VersionedStorage()) is None)
        self.assertEqual(count['count'], 0)

    def test_chain_with_list_and_postfix(self):
        'Chain with cases and postfix'
        def h(env, data, nh):
            self.assertEqual(env.count, 0)
            env['count'] = env['count'] + 1
            return nh(env, data)

        def h1(env, data, nh):
            self.assertEqual(env.count, 1)
            env['count'] = env['count'] + 1
            return nh(env, data)

        def h2(env, data, nh):
            self.assertEqual(env.count, 2)
            env['count'] = env['count'] + 1

        chain = web.handler(h) | web.cases(h1, web.handler(h1) | h2) | h2
        count = VersionedStorage(count=0)
        self.assert_(chain(count, VersionedStorage()) is None)
        self.assertEqual(count['count'], 0)

    def test_chain_of_lists(self):
        'Chain of lists, data check'
        def h(env, data, nx):
            data.count = 1
            return nx(env, data)

        def h1(env, data, nx):
            self.assert_('count' in data)
            self.assertEqual(data.count, 1)
            return nx(env, data)

        chain = web.cases(h) | web.cases(h1, h1)
        chain(VersionedStorage(), VersionedStorage())
