# -*- coding: utf-8 -*-

__all__ = ['Chain']

import unittest
from iktomi import web
from iktomi.web.core import _FunctionWrapper3
from iktomi.utils.storage import VersionedStorage
from webob.exc import HTTPNotFound

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
            env.count = env.count + 1
            return nh(env, data)

        @F
        def h2(env, data, nh):
            self.assertEqual(env.count, 0)
            env.count = env.count + 1
            return nh(env, data)

        @F
        def h3(env, data, nh):
            self.assertEqual(env.count, 0)
            env.count = env.count + 1
            return nh(env, data)

        chain = web.cases(h1, h2, h3)
        env = VersionedStorage(count=0)
        self.assert_(chain(env, VS()) is None)
        self.assertEqual(env.count, 0)

    def test_list_of_chains(self):
        'cases of chains'

        @F
        def h1(env, data, nh):
            self.assertEqual(env.count, 0)
            env.count = env.count + 1
            return nh(env, data)

        @F
        def h2(env, data, nh):
            self.assertEqual(env.count, 0)
            env.count = env.count + 1
            return nh(env, data)

        @F
        def h3(env, data, nh):
            self.assertEqual(env.count, 1)
            env.count = env.count + 1
            return nh(env, data)

        chain = web.cases(h1, h2 | h3)
        env = VS(count=0)
        self.assert_(chain(env, VS()) is None)
        self.assertEqual(env.count, 0)

    def test_chain_with_list(self):
        'Chain with cases'
        @F
        def h(env, data, nh):
            self.assertEqual(env.count, 0)
            env.count = env.count + 1
            return nh(env, data)

        @F
        def h1(env, data, nh):
            self.assertEqual(env.count, 1)
            env.count = env.count + 1
            return nh(env, data)

        @F
        def h2(env, data, nh):
            self.assertEqual(env.count, 2)
            env.count = env.count + 1
            return nh(env, data)

        chain = h | web.cases(h1, h1 | h2)
        env = VS(count=0)
        self.assert_(chain(env, VS()) is None)
        self.assertEqual(env.count, 1)

    def test_chain_with_list_and_postfix(self):
        'Chain with cases and postfix'
        @F
        def h(env, data, nh):
            self.assertEqual(env.count, 0)
            env.count = env.count + 1
            return nh(env, data)

        @F
        def h1(env, data, nh):
            self.assertEqual(env.count, 1)
            env.count = env.count + 1
            return nh(env, data)

        @F
        def h2(env, data, nh):
            self.assertEqual(env.count, 2)
            env.count = env.count + 1

        chain = h | web.cases(h1 | h2, h1) | h2
        env = VS(count=0)
        self.assertEqual(chain(env, VS()), None)
        self.assertEqual(env.count, 1)

    def test_chain_of_lists(self):
        'Chain of lists, data check'
        @F
        def h(env, data, nx):
            data.count = 1
            return nx(env, data)

        @F
        def h1(env, data, nx):
            self.assert_(hasattr(data, 'count'))
            self.assertEqual(data.count, 1)
            return nx(env, data)

        chain = web.cases(h) | web.cases(h1, h1)
        chain(VS(), VS())

    def test_chain_reuse_handler(self):
        'Reuse handlers'
        @F
        def h(env, data, nx):
            count = nx(env, data) or 0
            return count + 1

        chain = h | h | h | h
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
        @F
        def h(env, data, nx):
            count = nx(env, data) or 0
            return count + 1

        chain = h | web.cases(h, h)
        chain1 = chain | h
        chain2 = chain | h
        chain3 = chain2 | h

        self.assertEqual(chain1(VS(), VS()), 3)
        self.assertEqual(chain2(VS(), VS()), 3)
        self.assertEqual(chain3(VS(), VS()), 4)

    def test_chain_reuse_cases(self):
        'Reuse cases handler'
        @F
        def h(env, data, nx):
            count = nx(env, data) or 0
            return count + 1

        chain = h | h | h
        chain = h
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

    def test_chain_to_cases_with_functions(self):
        @F
        def h(env, data, nx):
            count = nx(env, data) or 0
            return count + 1

        def e(env, data):
            return 10

        chain = web.cases(h | e, h) | h
        self.assertEqual(chain(VS(), VS()), 11)

        chain = web.cases(e, h) | h
        self.assertEqual(chain(VS(), VS()), 10)

    def test_response_chaining(self):
        # make shure that webob responses can be used twice
        #wsgi_response = {}
        #def start_response(status, headers):
        #    wsgi_response['status'] = int(status.split()[0])
        #    wsgi_response['headers'] = headers

        nf = HTTPNotFound()
        chain = web.request_filter(lambda e,d,n: n(e,d)) | nf
        response = chain(VS(), VS())
        self.assert_(response is nf)
        #resp = response({'REQUEST_METHOD': 'GET'}, start_response)
        #self.assert_('404' in resp[0])
        #self.assertEqual(wsgi_response['status'], 404)

        #response = chain(VS(), VS())
        #self.assert_(response is nf)
        #resp = response({'REQUEST_METHOD': 'GET'}, start_response)
        #self.assert_('404' in resp[0])
        #self.assertEqual(wsgi_response['status'], 404)

    def test_response_class_chaining(self):
        nf = HTTPNotFound
        chain = web.request_filter(lambda e,d,n: n(e,d)) | nf
        response = chain(VS(), VS())
        self.assert_(isinstance(response, nf))
 
