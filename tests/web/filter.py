# -*- coding: utf-8 -*-

import unittest
import sys
import os
FRAMEWORK_DIR = os.path.abspath('../..')
sys.path.append(FRAMEWORK_DIR)
from insanities.web.core import Map, RequestHandler, ContinueRoute
from insanities.web.filters import *
from insanities.web.wrappers import *
from insanities.web.http import Request, RequestContext


class Prefix(unittest.TestCase):

    def test_prefix_root(self):
        '''Prefix root'''

        def handler(r):
            self.assertEqual(r.request.path, '/')

        app = Map(
            match('/', 'index') | handler,
            prefix('/docs') | Map(
                match('/', 'docs') | handler,
                match('/item', 'doc') | handler,
                prefix('/tags') | Map(
                    match('/', 'tags') | handler,
                    match('/tag', 'tag') | handler
                )
            )
        )
        
        def assertStatus(url, st):
            rctx = RequestContext(Request.blank(url).environ)
            self.assertEqual(app(rctx).response.status_int, st)
        
        assertStatus('/docs', 200)
        assertStatus('/docs/', 200)
        assertStatus('/docs/tags', 200)
        assertStatus('/docs/tags/', 200)
        # assert assertStatus works correct
        assertStatus('/docs/tags/asdasd', 404) 

    def test_prefix_leaf(self):
        '''Simple prefix'''

        def handler(r):
            self.assertEqual(r.request.path, '/item')

        app = Map(
            match('/', 'index') | handler,
            prefix('/docs') | Map(
                match('/', 'docs') | handler,
                match('/item', 'doc') | handler,
                prefix('/tags') | Map(
                    match('/', 'tags') | handler,
                    match('/tag', 'tag') | handler
                )
            )
        )

        rctx = RequestContext(Request.blank('/docs/item').environ)
        self.assertEqual(app(rctx).response.status_int, 200)


class Subdomain(unittest.TestCase):

    def test_subdomain(self):
        '''Subdomain filter'''

        def handler(r):
            self.assertEqual(r.request.path, '/')

        app = subdomain('host') | Map(
            subdomain('') | match('/', 'index') | handler,
            subdomain('k') | Map(
                subdomain('l') | Map(
                    match('/', 'l') | handler,
                ),
                subdomain('') | match('/', 'k') | handler,
            )
        )
        app = Map(app)
        
        def assertStatus(url, st):
            rctx = RequestContext(Request.blank(url).environ)
            self.assertEqual(app(rctx).response.status_int, st)

        assertStatus('http://host/', 200)
        assertStatus('http://k.host/', 200)
        assertStatus('http://l.k.host/', 200)
        assertStatus('http://x.l.k.host/', 200) # XXX: Is it right?
        assertStatus('http://x.k.host/', 404)
        assertStatus('http://lk.host/', 404)
        assertStatus('http://mhost/', 404) # XXX: we need a method to set root
                                           #domain without chaining subdomain to the map


class Match(unittest.TestCase):

    def test_simple_match(self):
        '''Check simple case of match'''

        m = match('/first', 'first')

        rctx = RequestContext(Request.blank('/first').environ)
        rctx = m(rctx)
        self.assertEqual(rctx.response.status_int, 200)
        rctx = RequestContext(Request.blank('/second').environ)
        self.assertRaises(ContinueRoute, lambda : m(rctx))

    def test_int_converter(self):
        '''Check int converter'''

        def handler(r):
            self.assertEqual(r.template_data.id, 42)

        app = Map(
            match('/first', 'first') | handler,
            match('/second/<int:id>', 'second') | handler
        )

        rctx = RequestContext(Request.blank('/second/42').environ)
        app(rctx)

    def test_multiple_int_convs(self):
        '''Check multiple int converters'''

        def handler(r, id, param):
            self.assertEqual(id, 42)
            self.assertEqual(param, 23)

        app = Map(
            match('/first', 'first') | handler,
            match('/second/<int:id>/<int:param>', 'second') | handler
        )

        rctx = RequestContext(Request.blank('/second/42/23').environ)
        app(rctx)

    def test_handler_with_param(self):
        '''Check int converter with handler which accepts params'''

        def handler(r, id):
            self.assertEqual(id, 42)

        app = Map(
            match('/first', 'first') | handler,
            match('/second/<int:id>', 'second') | handler
        )

        rctx = RequestContext(Request.blank('/second/42').environ)
        app(rctx)

    def test_not_found(self):
        '''Check int converter with handler which accepts params'''

        def handler(r, id):
            pass

        app = Map(
            match('/first', 'first') | handler,
            match('/second/<int:id>', 'second') | handler
        )

        rctx = RequestContext.blank('/second/42/')
        app(rctx)
        self.assertEqual(rctx.response.status_int, 404)
        rctx = RequestContext.blank('/second/42s')
        app(rctx)
        self.assertEqual(rctx.response.status_int, 404)
