# -*- coding: utf-8 -*-

import unittest
import sys
import os
FRAMEWORK_DIR = os.path.abspath('../..')
sys.path.append(FRAMEWORK_DIR)
from insanities.web.core import Map, RequestHandler, Reverse
from insanities.web.filters import *
from insanities.web.wrappers import *
from insanities.web.http import RequestContext

class MapInit(unittest.TestCase):

    def test_function_handler(self):
        '''Function as handler'''
        def handler(r):
            pass
        app = Map(handler)
        self.assert_(len(app.handlers) == 1)
        first_item = app.handlers[0]
        self.assert_(isinstance(first_item, RequestHandler))

    def test_functions_chain(self):
        '''Functions as a chain of handlers'''
        def handler1(r):
            pass

        def handler2(r):
            pass

        app = Map(
            RequestHandler() | handler1 | handler2
        )
        self.assert_(len(app.handlers) == 1)
        first_item = app.handlers[0]
        self.assert_(isinstance(first_item._next_handler, RequestHandler))
        self.assert_(first_item._next_handler.func is handler1)
        self.assert_(first_item._next_handler._next_handler.func is handler2)

    def test_usual_request_handlers(self):
        rh1 = RequestHandler()
        rh2 = RequestHandler()
        app = Map(
            rh1 | rh2
        )
        self.assert_(len(app.handlers) == 1)
        first_item = app.handlers[0]
        self.assert_(first_item is rh1)
        self.assert_(first_item._next_handler is rh2)

    def test_function_argspec(self):
        'ARGSPEC'

        def handler(r, a, b=None):
            self.assertEqual(a, 'a')
            self.assert_(b in [None, 'b'])

        app = Map(
            match('/<string:a>', 'a') | handler,
            match('/<string:a>/<string:b>', 'b') | handler,
        )

        rctx = RequestContext.blank('/a')
        app(rctx)
        rctx = RequestContext.blank('/a/b')
        app(rctx)


class MapReverse(unittest.TestCase):

    def test_simple_urls(self):
        '''Stright match'''

        def handler(r):
            pass

        app = Map(
            match('/', 'index') | handler,
            match('/docs', 'docs') | handler,
            match('/items/all', 'all') | handler)
        url_for = lambda x: unicode(Reverse(app.urls, '')(x))
        self.assertEqual(url_for('index'), '/')
        self.assertEqual(url_for('docs'), '/docs')
        self.assertEqual(url_for('all'), '/items/all')

        def fail():
            url_for('notHeare')

        self.assertRaises(KeyError, fail)

    def test_nested_map(self):
        '''Nested Maps'''
        def handler(r):
            pass

        app = Map(
            match('/', 'index') | handler,
            match('/docs', 'docs') | handler,
            match('/items/all', 'all') | handler,
            Map(
                match('/nested/', 'nested') | handler
            )
        )
        url_for = lambda x: unicode(Reverse(app.urls, '')(x))
        self.assertEqual(url_for('index'), '/')
        self.assertEqual(url_for('docs'), '/docs')
        self.assertEqual(url_for('all'), '/items/all')
        self.assertEqual(url_for('nested'), '/nested/')

    def test_nested_map_with_ns(self):
        '''Nested Maps with namespace'''
        def handler(r):
            pass

        app = Map(
            match('/', 'index') | handler,
            match('/docs', 'docs') | handler,
            match('/items/all', 'all') | handler,
            namespace('nested') | Map(
                match('/nested/', 'item') | handler
            ),
            Map(
                match('/other/', 'other') | handler
            )
        )
        url_for = lambda x: unicode(Reverse(app.urls, '')(x))
        self.assertEqual(url_for('index'), '/')
        self.assertEqual(url_for('docs'), '/docs')
        self.assertEqual(url_for('all'), '/items/all')
        self.assertEqual(url_for('nested.item'), '/nested/')
        self.assertEqual(url_for('other'), '/other/')

        self.assertRaises(KeyError, lambda: url_for('nested'))

    def test_nested_maps_with_ns(self):
        '''Nested Maps with namespace'''
        def handler(r):
            pass

        app = Map(
            match('/', 'index') | handler,
            match('/docs', 'docs') | handler,
            match('/items/all', 'all') | handler,
            namespace('nested') | Map(
                match('/nested/', 'item') | handler
            ),
            namespace('other') | Map(
                match('/other/', 'item') | handler
            ),
            Map(
                match('/other/', 'other') | handler
            )
        )
        url_for = lambda x: unicode(Reverse(app.urls, '')(x))
        self.assertEqual(url_for('index'), '/')
        self.assertEqual(url_for('docs'), '/docs')
        self.assertEqual(url_for('all'), '/items/all')
        self.assertEqual(url_for('nested.item'), '/nested/')
        self.assertEqual(url_for('other'), '/other/')
        self.assertEqual(url_for('other.item'), '/other/')

        self.assertRaises(KeyError, lambda: url_for('nested'))

    def test_nested_namespaces(self):
        '''Reversing urls with nested namespaces'''
        def handler(r): pass

        urls = {}
        def write_urls(rctx):
            urls['local'] = rctx.vals.url_for('all')
            #XXX: this is not normal!
            urls['parent'] = rctx.vals.url_for('ru.about.contacts')
            urls['global'] = rctx.vals.url_for('en.news.all')

        site = Map(
            prefix('/news') | namespace('news') | Map(
                match('/test', 'test') | write_urls,
                match('/all', 'all') | handler
            ),
            prefix('/about') | namespace('about') | Map(
                match('/contacts', 'contacts') | handler
            )
        )

        app = Map(
            prefix('/en') | namespace('en') | site,
            prefix('/ru') | namespace('ru') | site,
        )

        rctx = RequestContext.blank('/ru/news/test')
        app(rctx)

        self.assertEqual(str(urls['local']), '/ru/news/all')
        self.assertEqual(str(urls['global']), '/en/news/all')
        self.assertEqual(str(urls['parent']), '/ru/about/contacts')
        # will we fix this or not?
        # If we will we have to discover all usecases and write additional tests


    def test_subdomain(self):
        '''Subdomain reverse'''

        def handler(r):
            pass

        app = subdomain('host') | Map(
            subdomain('') | match('/', 'index') | handler,
            subdomain('k') | Map(
                subdomain('l') | Map(
                    match('/', 'l') | handler,
                    match('/url/', 'l1') | handler,
                    prefix('/my') | match('/url/', 'l2') | handler,
                ),
                subdomain('') | match('/', 'k') | handler,
            )
        )
        app = Map(app)

        url_for = lambda x: unicode(Reverse(app.urls, '')(x))
        self.assertEqual(url_for('index'), 'http://host/')
        self.assertEqual(url_for('k'), 'http://k.host/')
        self.assertEqual(url_for('l'), 'http://l.k.host/')
        self.assertEqual(url_for('l1'), 'http://l.k.host/url/')
        self.assertEqual(url_for('l2'), 'http://l.k.host/my/url/')


    def test_double_match(self):
        '''Check double match'''

        def handler(r):
            self.assertEqual(r.request.path, '/first')

        self.assertRaises(ValueError, lambda : Map(
            match('/first/', 'other') | handler,
            match('/first', 'first') | handler,
            match('/second', 'second') | handler,
            match('/second', 'second') | handler)
        )

    def test_repeated_chaining(self):
        '''Check second usage of handlers in chaining'''

        class Write(RequestHandler):
            def __init__(self, letter):
                RequestHandler.__init__(self)
                self.letter = letter
            def handle(self, rctx):
                rctx.log = getattr(rctx, 'log', '') + self.letter
                return rctx

        w1, w2, w3 = Write('1'), Write('2'), Write('3')

        ch1 = w1 | w2
        ch2 = w1 | w3 # this chain has side-effect!

        rctx = RequestContext.blank('')
        rctx = ch1(rctx)
        self.assertEqual(rctx.log, '12') # got '123'. wtf?

        rctx = RequestContext.blank('')
        ch2(rctx)
        self.assertEqual(rctx.log, '13')
