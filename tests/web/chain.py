# -*- coding: utf-8 -*-

__all__ = ['Chain']

import unittest
from iktomi import web
from iktomi.web.core import _FunctionWrapper3
from iktomi.utils.storage import VersionedStorage

skip = getattr(unittest, 'skip', lambda x: None)
VS = VersionedStorage
F = web.request_filter


class Chain(unittest.TestCase):

    def test_functions_chain(self):
        '''Functions as a chain of handlers'''

        def handler1(env, data, nh):
            return nh(env, data)

        def handler2(env, data, nh):
            return nh(env, data)

        def handler3(env, data):
            return None

        chain = F(handler1) | F(handler2) | handler3

        handler = chain._next_handler
        self.assert_(isinstance(handler, _FunctionWrapper3))
        self.assertEqual(handler.handler, handler2)

        handler = chain._next_handler._next_handler
        self.assertEqual(handler, handler3)

    def test_functions_chain_call(self):
        'Functions chain call'

        @F
        def handler1(env, data, nh):
            return nh(env, data)

        @F
        def handler2(env, data, nh):
            return nh(env, data)

        chain = handler1 | handler2

        self.assert_(chain(VS(), VS()) is None)

    def test_List(self):
        'cases handle'
        @F
        def h1(env, data, nh):
            self.assertEqual(env.count, 0)
            env['count'] = env['count'] + 1
            return nh(env, data)

        @F
        def h2(env, data, nh):
            self.assertEqual(env.count, 0)
            env['count'] = env['count'] + 1
            return nh(env, data)

        @F
        def h3(env, data, nh):
            self.assertEqual(env.count, 0)
            env['count'] = env['count'] + 1
            return nh(env, data)

        chain = web.cases(h1, h2, h3)
        count = VersionedStorage(count=0)
        self.assert_(chain(count, VS()) is None)
        self.assertEqual(count['count'], 0)

    def test_list_of_chains(self):
        'cases of chains'

        @F
        def h1(env, data, nh):
            self.assertEqual(env.count, 0)
            env['count'] = env['count'] + 1
            return nh(env, data)

        @F
        def h2(env, data, nh):
            self.assertEqual(env.count, 0)
            env['count'] = env['count'] + 1
            return nh(env, data)

        @F
        def h3(env, data, nh):
            self.assertEqual(env.count, 1)
            env['count'] = env['count'] + 1
            return nh(env, data)

        chain = web.cases(h1, h2 | h3)
        count = VS(count=0)
        self.assert_(chain(count, VS()) is None)
        self.assertEqual(count['count'], 0)

    def test_chain_with_list(self):
        'Chain with cases'
        @F
        def h(env, data, nh):
            self.assertEqual(env.count, 0)
            env['count'] = env['count'] + 1
            return nh(env, data)

        @F
        def h1(env, data, nh):
            self.assertEqual(env.count, 1)
            env['count'] = env['count'] + 1
            return nh(env, data)

        @F
        def h2(env, data, nh):
            self.assertEqual(env.count, 2)
            env['count'] = env['count'] + 1
            return nh(env, data)

        chain = h | web.cases(h1, h1 | h2)
        count = VS(count=0)
        self.assert_(chain(count, VS()) is None)
        self.assertEqual(count['count'], 1)

    def test_chain_with_list_and_postfix(self):
        'Chain with cases and postfix'
        @F
        def h(env, data, nh):
            self.assertEqual(env.count, 0)
            env['count'] = env['count'] + 1
            return nh(env, data)

        @F
        def h1(env, data, nh):
            self.assertEqual(env.count, 1)
            env['count'] = env['count'] + 1
            return nh(env, data)

        @F
        def h2(env, data, nh):
            self.assertEqual(env.count, 2)
            env['count'] = env['count'] + 1

        chain = h | web.cases(h1 | h2, h1) | h2
        count = VS(count=0)
        self.assertEqual(chain(count, VS()), None)
        self.assertEqual(count['count'], 1)

    def test_chain_of_lists(self):
        'Chain of lists, data check'
        @F
        def h(env, data, nx):
            data.count = 1
            return nx(env, data)

        @F
        def h1(env, data, nx):
            self.assert_('count' in data)
            self.assertEqual(data.count, 1)
            return nx(env, data)

        chain = web.cases(h) | web.cases(h1, h1)
        chain(VS(), VS())

    def test_chain_reuse_handler(self):
        'Reuse handlers'
        def h(env, data, nx):
            count = nx(env, data) or 0
            return count + 1

        h_wrapped = F(h)
        chain = h_wrapped | h_wrapped | h_wrapped | h_wrapped
        self.assertEqual(chain(VS(), VS()), 4)

    def test_chain_reuse_chain(self):
        'Reuse chains'
        def h(i):
            def h1(env, data, nx):
                count = nx(env, data) or 0
                return count + i
            return h1

        reusable = F(h(1)) | F(h(2))
        chain1 = F(h(4)) | reusable | F(h(8))
        chain2 = F(h(16)) | reusable | F(h(32))

        self.assertEqual(reusable(VS(), VS()), 3)
        self.assertEqual(chain1(VS(), VS()), 15)
        self.assertEqual(chain2(VS(), VS()), 51)

    def test_chain_reuse_handler2(self):
        'Reuse handlers, then use only first one and assert nothing has changed'
        def h(env, data, nx):
            count = nx(env, data) or 0
            return count + 1

        h_wrapped = F(h)
        chain = F(h) | web.cases(h_wrapped,
                                 h_wrapped)
        chain1 = chain | h_wrapped
        chain2 = chain | h_wrapped
        chain3 = chain2 | h_wrapped

        self.assertEqual(chain1(VS(), VS()), 3)
        self.assertEqual(chain2(VS(), VS()), 3)
        self.assertEqual(chain3(VS(), VS()), 4)

    def test_chain_reuse_cases(self):
        'Reuse cases handler'
        def h(env, data, nx):
            count = nx(env, data) or 0
            return count + 1

        h_wrapped = F(h)
        chain = h_wrapped | h_wrapped | h_wrapped
        chain = h_wrapped
        self.assertEqual(chain(VS(), VS()), 1)

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

