# -*- coding: utf-8 -*-

import unittest
import sys
import os
FRAMEWORK_DIR = os.path.abspath('../..')
sys.path.append(FRAMEWORK_DIR)
from insanities.web.core import Map, RequestHandler
from insanities.web.filters import *

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


class MapReverse(unittest.TestCase):

    def test_simple_urls(self):
        '''Stright match'''
        def handler(r):
            pass

        app = Map(
            match('/', 'index') | handler,
            match('/docs', 'docs') | handler,
            match('/items/all', 'all') | handler
        )
        self.assertEqual(app.url_for('index'), '/')
        self.assertEqual(app.url_for('docs'), '/docs')
        self.assertEqual(app.url_for('all'), '/items/all')

        def fail():
            app.url_for('notHeare')

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
        self.assertEqual(app.url_for('index'), '/')
        self.assertEqual(app.url_for('docs'), '/docs')
        self.assertEqual(app.url_for('all'), '/items/all')
        self.assertEqual(app.url_for('nested'), '/nested/')

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
        self.assertEqual(app.url_for('index'), '/')
        self.assertEqual(app.url_for('docs'), '/docs')
        self.assertEqual(app.url_for('all'), '/items/all')
        self.assertEqual(app.url_for('nested.item'), '/nested/')
        self.assertEqual(app.url_for('other'), '/other/')

        def fail():
            app.url_for('nested')

        self.assertRaises(KeyError, fail)

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
        self.assertEqual(app.url_for('index'), '/')
        self.assertEqual(app.url_for('docs'), '/docs')
        self.assertEqual(app.url_for('all'), '/items/all')
        self.assertEqual(app.url_for('nested.item'), '/nested/')
        self.assertEqual(app.url_for('other'), '/other/')
        self.assertEqual(app.url_for('other.item'), '/other/')

        def fail():
            app.url_for('nested')

        self.assertRaises(KeyError, fail)

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
