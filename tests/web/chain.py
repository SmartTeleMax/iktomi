# -*- coding: utf-8 -*-

__all__ = ['Chain']

import unittest
from insanities import web
from insanities.utils.stacked_dict import StackedDict


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
        self.assert_(isinstance(handler, web.handler))
        self.assertEqual(handler.func, handler2)

        handler = chain._next_handler._next_handler
        self.assert_(isinstance(handler, web.handler))
        self.assertEqual(handler.func, handler3)

    def test_functions_chain_call(self):
        'Functions chain call'

        def handler1(env, data, nh):
            return nh(env, data)

        def handler2(env, data, nh):
            return nh(env, data)

        chain = web.handler(handler1) | handler2

        self.assert_(chain(StackedDict(), StackedDict()) is None)

    def test_List(self):
        'List handle'
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

        chain = web.List(h1, h2, h3)
        count = StackedDict(count=0)
        self.assert_(chain(count, StackedDict()) is None)
        self.assertEqual(count['count'], 0)

    def test_list_of_chains(self):
        'List of chains'
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

        chain = web.List(h1, web.handler(h2) | h3)
        count = StackedDict(count=0)
        self.assert_(chain(count, StackedDict()) is None)
        self.assertEqual(count['count'], 0)

    def test_chain_with_list(self):
        'Chain with List'
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

        chain = web.handler(h) | web.List(h1, web.handler(h1) | h2)
        count = StackedDict(count=0)
        self.assert_(chain(count, StackedDict()) is None)
        self.assertEqual(count['count'], 0)

    def test_chain_with_list_and_postfix(self):
        'Chain with List and postfix'
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

        chain = web.handler(h) | web.List(h1, web.handler(h1) | h2) | h1
        count = StackedDict(count=0)
        self.assert_(chain(count, StackedDict()) is None)
        self.assertEqual(count['count'], 0)
