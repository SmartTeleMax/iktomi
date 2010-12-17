# -*- coding: utf-8 -*-

__all__ = ['UrlTemplateTests', 'Prefix', 'Match', 'Subdomain']

import unittest
from insanities import web
from insanities.web.url import UrlTemplate
from insanities.web.http import Request, Response
from insanities.utils.stacked_dict import StackedDict

class UrlTemplateTests(unittest.TestCase):

    def test_match_without_params(self):
        'UrlTemplate match method without params'
        ut = UrlTemplate('simple')
        self.assertEqual(ut.match('simple'), (True, {}))
        self.assertEqual(ut.match('/simple'), (False, {}))

    def test_match_with_params(self):
        'UrlTemplate match method with params'
        ut = UrlTemplate('/simple/<int:id>')
        self.assertEqual(ut.match('/simple/2'), (True, {'id':2}))
        self.assertEqual(ut.match('/simple'), (False, {}))
        self.assertEqual(ut.match('/simple/d'), (False, {}))

    def test_match_from_begining_without_params(self):
        'UrlTemplate match method without params (from begining of str)'
        ut = UrlTemplate('simple', match_whole_str=False)
        self.assertEqual(ut.match('simple'), (True, {}))
        self.assertEqual(ut.match('simple/sdffds'), (True, {}))
        self.assertEqual(ut.match('/simple'), (False, {}))
        self.assertEqual(ut.match('/simple/'), (False, {}))

    def test_match_from_begining_with_params(self):
        'UrlTemplate match method with params (from begining of str)'
        ut = UrlTemplate('/simple/<int:id>', match_whole_str=False)
        self.assertEqual(ut.match('/simple/2'), (True, {'id':2}))
        self.assertEqual(ut.match('/simple/2/sdfsf'), (True, {'id':2}))
        self.assertEqual(ut.match('/simple'), (False, {}))
        self.assertEqual(ut.match('/simple/d'), (False, {}))
        self.assertEqual(ut.match('/simple/d/sdfsdf'), (False, {}))

    def test_builder_without_params(self):
        'UrlTemplate builder method (without params)'
        ut = UrlTemplate('/simple')
        self.assertEqual(ut(), '/simple')

    def test_builder_with_params(self):
        'UrlTemplate builder method (with params)'
        ut = UrlTemplate('/simple/<int:id>/data')
        self.assertEqual(ut(id=2), '/simple/2/data')


class Prefix(unittest.TestCase):

    def test_prefix_root(self):
        '''Prefix root'''

        def handler(env, data, nx):
            self.assertEqual(env.request.prefixed_path, '/')
            return Reponse()

        app = web.List(
            web.match('/', 'index') | handler,
            web.prefix('/docs') | web.List(
                web.match('/', 'docs') | handler,
                web.match('/item', 'doc') | handler,
                web.prefix('/tags') | web.List(
                    web.match('/', 'tags') | handler,
                    web.match('/tag', 'tag') | handler
                )
            )
        )

        def assertStatus(url, status):
            env = StackedDict()
            env.request = Request.blank(url)
            self.assertEqual(app(env, {}).status_int, status)

        self.assert_(app(Request.blank('/docs'), {}) is STOP)
        assertStatus('/docs/', 200)
        self.assert_(app(Request.blank('/docs/tags'), {}) is STOP)
        assertStatus('/docs/tags/',200)
        self.assert_(app(Request.blank('/docs/tags/asdasd'), {}) is STOP)

    def test_prefix_leaf(self):
        '''Simple prefix'''

        def handler(r):
            self.assertEqual(r.request.prefixed_path, '/item')

        app = web.List(
            web.match('/', 'index') | handler,
            web.prefix('/docs') | web.List(
                web.match('/', 'docs') | handler,
                web.match('/item', 'doc') | handler,
                web.prefix('/tags') | web.List(
                    web.match('/', 'tags') | handler,
                    web.match('/tag', 'tag') | handler
                )
            )
        )

        rctx = RequestContext.blank('/docs/item')
        self.assertEqual(app(rctx).response.status_int, 200)

    def test_unicode(self):
        '''Routing rules with unicode'''
        app = web.List(
            web.prefix(u'/հայերեն') | web.List(
                web.match(u'/%', 'percent')
            )
        )
        encoded = '/%D5%B0%D5%A1%D5%B5%D5%A5%D6%80%D5%A5%D5%B6/%25'
        rctx = RequestContext.blank(encoded)

        self.assertEqual(str(Reverse(app.urls, '')('percent')), encoded)
        self.assertEqual(Reverse(app.urls, '')('percent').get_readable(), u'/հայերեն/%')

        self.assert_(app(rctx) is not STOP)

        # rctx have prefixes, so we need new one
        rctx = RequestContext.blank(encoded)
        self.assertEqual(app(rctx).response.status_int, 200)


class Subdomain(unittest.TestCase):

    def test_subdomain(self):
        '''Subdomain filter'''

        def handler(r):
            self.assertEqual(r.request.path, '/')

        app = web.subdomain('host') | web.List(
            web.subdomain('') | web.match('/', 'index') | handler,
            web.subdomain('k') | web.List(
                web.subdomain('l') | web.List(
                    web.match('/', 'l') | handler,
                ),
                web.subdomain('') | web.match('/', 'k') | handler,
            )
        )
        app = web.List(app)

        def assertStatus(url, st):
            rctx = RequestContext(Request.blank(url).environ)
            self.assertEqual(app(rctx).response.status_int, st)

        assertStatus('http://host/', 200)
        assertStatus('http://k.host/', 200)
        assertStatus('http://l.k.host/', 200)
        assertStatus('http://x.l.k.host/', 200) # XXX: Is it right?
        self.assert_(app(RequestContext.blank('http://x.k.host/')) is STOP)
        self.assert_(app(RequestContext.blank('http://lk.host/')) is STOP)
        self.assert_(app(RequestContext.blank('http://mhost/')) is STOP)

    def test_unicode(self):
        '''IRI tests'''
        app = web.List(web.subdomain(u'рф') | web.subdomain(u'сайт') | web.match('/', 'site'))
        encoded = 'http://xn--80aswg.xn--p1ai/'
        self.assertEqual(Reverse(app.urls, '')('site').get_readable(), u'http://сайт.рф/')
        self.assertEqual(str(Reverse(app.urls, '')('site')), encoded)

        rctx = RequestContext.blank(encoded)
        self.assert_(app(rctx) is not STOP)
        self.assertEqual(app(rctx).response.status_int, 200)


class Match(unittest.TestCase):

    def test_simple_match(self):
        '''Check simple case of match'''

        m = web.match('/first', 'first') | (lambda x: x)

        rctx = RequestContext(Request.blank('/first').environ)
        rctx = m(rctx)
        self.assert_(rctx.response.status_int, 200)
        rctx = RequestContext(Request.blank('/second').environ)
        rctx = m(rctx)
        self.assert_(rctx is STOP)

    def test_int_converter(self):
        '''Check int converter'''

        def handler(r):
            self.assertEqual(r.data.id, 42)

        app = web.List(
            web.match('/first', 'first') | handler,
            web.match('/second/<int:id>', 'second') | handler
        )

        rctx = RequestContext(Request.blank('/second/42').environ)
        app(rctx)

    def test_multiple_int_convs(self):
        '''Check multiple int converters'''

        def handler(r, id, param):
            self.assertEqual(id, 42)
            self.assertEqual(param, 23)

        app = web.List(
            web.match('/first', 'first') | handler,
            web.match('/second/<int:id>/<int:param>', 'second') | handler
        )

        rctx = RequestContext(Request.blank('/second/42/23').environ)
        app(rctx)

    def test_handler_with_param(self):
        '''Check int converter with handler which accepts params'''

        def handler(r, id):
            self.assertEqual(id, 42)

        app = web.List(
            web.match('/first', 'first') | handler,
            web.match('/second/<int:id>', 'second') | handler
        )

        rctx = RequestContext(Request.blank('/second/42').environ)
        app(rctx)

    def test_not_found(self):
        '''Check int converter with handler which accepts params'''

        def handler(r, id):
            pass

        app = web.List(
            web.match('/first', 'first') | handler,
            web.match('/second/<int:id>', 'second') | handler
        )

        rctx = app(RequestContext.blank('/second/42/'))
        self.assert_(rctx is STOP)
        rctx = app(RequestContext.blank('/second/42s'))
        self.assert_(rctx is STOP)
