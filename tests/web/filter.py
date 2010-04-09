# -*- coding: utf-8 -*-

import unittest
import sys
import os
FRAMEWORK_DIR = os.path.abspath('../..')
sys.path.append(FRAMEWORK_DIR)
from insanities.web.core import Map, Chain, RequestHandler, ContinueRoute
from insanities.web.filters import *
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

        rctx = RequestContext(Request.blank('/docs').environ)
        app(rctx)
        rctx = RequestContext(Request.blank('/docs/').environ)
        app(rctx)
        rctx = RequestContext(Request.blank('/docs/tags').environ)
        app(rctx)
        rctx = RequestContext(Request.blank('/docs/tags/').environ)
        app(rctx)

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
        app(rctx)

    def test_prefix_data_transmit(self):
        '''Check how data is transmited throw map to map'''

        def handler(r):
            self.assert_(r.data.has_key('data_key'), 'Data is not transmitting')

        def data_setter(r):
            r.add_data(data_key='some data')
            ContinueRoute('data_setter')

        app = Map(
            data_setter,
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
        app(rctx)
        rctx = RequestContext(Request.blank('/docs/tags/').environ)
        app(rctx)
        rctx = RequestContext(Request.blank('/docs/tags/tag').environ)
        app(rctx)


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
            self.assertEqual(r.data['id'], 42)

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

        rctx = RequestContext(Request.blank('/second/42/').environ)
        app(rctx)
        self.assertEqual(rctx.response.status_int, 404)
        rctx = RequestContext(Request.blank('/second/42s').environ)
        app(rctx)
        self.assertEqual(rctx.response.status_int, 404)
