# -*- coding: utf-8 -*-

__all__ = ['UrlTemplateTests', 'Prefix', 'Match', 'Subdomain']

import unittest
from insanities import web
from insanities.web.url import UrlTemplate
from insanities.web.http import Request, Response

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
            self.assertEqual(env._route_state.path, '/')
            return Response()

        app = web.cases(
            web.match('/', 'index') | handler,
            web.prefix('/docs') | web.cases(
                web.match('/', 'docs') | handler,
                web.match('/item', 'doc') | handler,
                web.prefix('/tags') | web.cases(
                    web.match('/', 'tags') | handler,
                    web.match('/tag', 'tag') | handler)))

        self.assertEqual(web.ask(app, '/docs'), None)
        self.assertEqual(web.ask(app, '/docs/').status_int, 200)
        self.assertEqual(web.ask(app, '/docs/tags'), None)
        self.assertEqual(web.ask(app, '/docs/tags/').status_int, 200)
        self.assertEqual(web.ask(app, '/docs/tags/asdasd'), None)

    def test_prefix_leaf(self):
        '''Simple prefix'''

        def handler(env, data, nx):
            self.assertEqual(env._route_state.path, '/item')
            return Response()

        app = web.cases(
            web.match('/', 'index'),
            web.prefix('/docs') | web.cases(
                web.match('/', 'docs') | handler,
                web.match('/item', 'doc') | handler,
                web.prefix('/tags') | web.cases(
                    web.match('/', 'tags') | handler,
                    web.match('/tag', 'tag') | handler)))

        self.assertEqual(web.ask(app, '/docs/item').status_int, 200)

    def test_prefix_state(self):
        '''Prefix state correctness'''

        def handler(env, data, nx):
            return Response()

        app = web.cases(
            web.match('/', 'index'),
            web.prefix('/docs') | web.namespace('doc') | web.cases(
                web.match('/item', '') | handler,
                web.prefix('/list') | web.cases(
                    web.match('/item', 'list') | handler),
                web.match('/other-thing', 'something') | handler
                ),
            web.match('/something', 'something') | handler)

        self.assertEqual(web.ask(app, '/docs/something'), None)
        self.assertEqual(web.ask(app, '/docs/list/something'), None)
        self.assertEqual(web.ask(app, '/docs/list/other-thing'), None)


    def test_unicode(self):
        '''Routing rules with unicode'''
        # XXX move to urltemplate and reverse tests?
        app = web.cases(
            web.prefix(u'/հայերեն') | web.cases(
                web.match(u'/%', 'percent') | (lambda e,d,n: Response())
            )
        )
        encoded = '/%D5%B0%D5%A1%D5%B5%D5%A5%D6%80%D5%A5%D5%B6/%25'

        self.assertEqual(web.Reverse.from_handler(app)('percent'), encoded)
        self.assertEqual(web.Reverse.from_handler(app)('percent').get_readable(), u'/հայերեն/%')

        self.assertNotEqual(web.ask(app, encoded), None)

        # ???
        # rctx have prefixes, so we need new one
        self.assertEqual(web.ask(app, encoded).status_int, 200)


class Subdomain(unittest.TestCase):

    def test_subdomain(self):
        '''Subdomain filter'''

        def handler(env, data, nx):
            self.assertEqual(env.request.path, '/')
            return Response()

        app = web.subdomain('host') | web.cases(
            web.subdomain('') | web.match('/', 'index') | handler,
            web.subdomain('k') | web.cases(
                web.subdomain('l') | web.cases(
                    web.match('/', 'l') | handler,
                ),
                web.subdomain('') | web.match('/', 'k') | handler))

        self.assertEqual(web.ask(app, 'http://host/').status_int, 200)
        self.assertEqual(web.ask(app, 'http://k.host/').status_int, 200)
        self.assertEqual(web.ask(app, 'http://l.k.host/').status_int, 200)
        self.assertEqual(web.ask(app, 'http://x.l.k.host/').status_int, 200)
        self.assert_(web.ask(app, 'http://x.k.host/') is None)
        self.assert_(web.ask(app, 'http://lk.host/') is None)
        self.assert_(web.ask(app, 'http://mhost/') is None)

    def test_unicode(self):
        '''IRI tests'''
        app = web.subdomain(u'рф') | web.subdomain(u'сайт') | web.match('/', 'site') | (lambda e,d,n: Response() )
        encoded = 'http://xn--80aswg.xn--p1ai/'
        self.assertEqual(web.Reverse.from_handler(app)('site').get_readable(), u'http://сайт.рф/')
        self.assertEqual(web.Reverse.from_handler(app)('site'), encoded)
        self.assertNotEqual(web.ask(app, encoded), None)


class Match(unittest.TestCase):

    def test_simple_match(self):
        '''Check simple case of match'''

        app = web.match('/first', 'first') | (lambda env, data, nx: Response())

        self.assertEqual(web.ask(app, '/first').status_int, 200)
        self.assertEqual(web.ask(app, '/second'), None)

    def test_int_converter(self):
        '''Check int converter'''

        def handler(env, data, nx):
            self.assertEqual(data.id, 42)
            return Response()

        app = web.cases(
            web.match('/first', 'first') | handler,
            web.match('/second/<int:id>', 'second') | handler)

        web.ask(app, '/second/42')

    def test_multiple_int_convs(self):
        '''Check multiple int converters'''

        def handler(env, data, nx):
            self.assertEqual(data.id, 42)
            self.assertEqual(data.param, 23)
            return Response()

        app = web.cases(
            web.match('/first', 'first') | handler,
            web.match('/second/<int:id>/<int:param>', 'second') | handler)

        web.ask(app, '/second/42/23')

    def test_not_found(self):
        '''Check int converter with handler which accepts params'''

        def handler(env, data, nx):
            return Response()

        app = web.cases(
            web.match('/first', 'first') | handler,
            web.match('/second/<int:id>', 'second') | handler)

        self.assert_(web.ask(app, '/second/42/') is None)
        self.assert_(web.ask(app, '/second/42s') is None)

    def test_sane_exeptions(self):
        'Not yet completed test of sane exceptions'
        def get_items(env, data, nxt):
            return nxt(env, data)
        def raise_exc(env, data, nxt):
            raise Exception('somewhere deep inside')
        app = web.prefix('/prefix') | web.match('/', '') | get_items | raise_exc
        self.assertRaises(Exception, lambda: web.ask(app, '/prefix/'))
