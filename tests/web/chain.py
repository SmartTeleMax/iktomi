# -*- coding: utf-8 -*-

__all__ = ['Chain']

import unittest
from insanities import web
from insanities.web.core import _FunctionWrapper
from insanities.utils.storage import VersionedStorage

skip = getattr(unittest, 'skip', lambda x: None)

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

    def test_chain_reuse_handler(self):
        'Reuse handlers'
        def h(env, data, nx):
            count = nx(env, data) or 0
            return count + 1

        h_wrapped = web.handler(h)
        chain = h_wrapped | h_wrapped | h_wrapped | h_wrapped
        self.assertEqual(chain(VersionedStorage(), VersionedStorage()), 4)

    def test_chain_reuse_chain(self):
        'Reuse chains'
        def h(i):
            def h1(env, data, nx):
                count = nx(env, data) or 0
                return count + i
            return h1

        reusable = web.handler(h(1)) | h(2)
        chain1 = web.handler(h(4)) | reusable | h(8)
        chain2 = web.handler(h(16)) | reusable | h(32)

        self.assertEqual(reusable(VersionedStorage(), VersionedStorage()), 3)
        self.assertEqual(chain1(VersionedStorage(), VersionedStorage()), 15)
        self.assertEqual(chain2(VersionedStorage(), VersionedStorage()), 51)

    def test_chain_reuse_handler2(self):
        'Reuse handlers, then use only first one and assert nothing has changed'
        def h(env, data, nx):
            count = nx(env, data) or 0
            return count + 1

        h_wrapped = web.handler(h)
        chain = web.handler(h) | web.cases(h_wrapped,
                                      h_wrapped)
        chain1 = chain | h_wrapped
        chain2 = chain | h_wrapped
        chain3 = chain2 | h_wrapped

        self.assertEqual(chain1(VersionedStorage(), VersionedStorage()), 3)
        self.assertEqual(chain2(VersionedStorage(), VersionedStorage()), 3)
        self.assertEqual(chain3(VersionedStorage(), VersionedStorage()), 4)

    def test_chain_reuse_cases(self):
        'Reuse cases handler'
        def h(env, data, nx):
            count = nx(env, data) or 0
            return count + 1

        h_wrapped = web.handler(h)
        chain = h_wrapped | h_wrapped | h_wrapped
        chain = h_wrapped
        self.assertEqual(chain(VersionedStorage(), VersionedStorage()), 1)

    @skip
    def test_chain_reuse_copy_count(self):
        'Assert chaining does not cause too much copy calls'
        class CountHandler(web.WebHandler):
            copies = 0

            def __init__(self, i, *args, **kwargs):
                self.i = i
                web.WebHandler.__init__(self, *args, **kwargs)

            def copy(self):
                CountHandler.copies += 1
                cp = web.WebHandler.copy(self)
                assert isinstance(cp, CountHandler)
                return cp

        CountHandler(1) | CountHandler(2) | CountHandler(3)| CountHandler(4)| \
            CountHandler(5)| CountHandler(6)| CountHandler(7)

        self.assertEqual(CountHandler.copies, 7)

