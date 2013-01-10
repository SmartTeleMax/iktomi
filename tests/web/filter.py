# -*- coding: utf-8 -*-

__all__ = ['UrlTemplateTests', 'Prefix', 'Match', 'Subdomain']

import unittest
from iktomi import web
from iktomi.web.url_templates import UrlTemplate
from iktomi.web.http import Request, Response


class UrlTemplateTests(unittest.TestCase):

    def test_empty_match(self):
        'UrlTemplate match method with empty template'
        ut = UrlTemplate('')
        self.assertEqual(ut.match(''), (True, {}))
        self.assertEqual(ut.match('/'), (False, {}))

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

    def test_only_converter_is_present(self):
        ut = UrlTemplate('<int:id>')
        self.assertEqual(ut(id=2), '2')

    def test_default_converter(self):
        ut = UrlTemplate('<message>')
        self.assertEqual(ut(message='hello'), 'hello')

    def test_redefine_converters(self):
        from iktomi.web.url_converters import Integer

        class DoubleInt(Integer):
            def to_python(self, value, env=None):
                return Integer.to_python(self, value, env) * 2
            def to_url(self, value):
                return str(value / 2)

        ut = UrlTemplate('/simple/<int:id>',
                         converters=(DoubleInt,))
        self.assertEqual(ut(id=2), '/simple/1')
        self.assertEqual(ut.match('/simple/1'), (True, {'id': 2}))

    def test_var_name_with_underscore(self):
        ut = UrlTemplate('<message_uid>')
        self.assertEqual(ut(message_uid='uid'), 'uid')

    def test_trailing_delimiter(self):
        self.assertRaises(ValueError, UrlTemplate, '<int:id:>')

    def test_empty_param(self):
        self.assertRaises(ValueError, UrlTemplate, '<>')

    def test_delimiter_only(self):
        self.assertRaises(ValueError, UrlTemplate, '<:>')

    def test_type_and_delimiter(self):
        self.assertRaises(ValueError, UrlTemplate, '<int:>')

    def test_empty_type(self):
        self.assertRaises(ValueError, UrlTemplate, '<:id>')

    def test_no_delimiter(self):
        self.assertRaises(ValueError, UrlTemplate, '<any(x,y)slug>')


class Prefix(unittest.TestCase):

    def test_prefix_root(self):
        '''Prefix root'''

        def handler(env, data):
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

        def handler(env, data):
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

        def handler(env, data):
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

    def test_namespace_with_dot(self):
        app = web.cases(
                web.namespace("english.docs.news") | web.match('/item', 'item'),
                )
        r = web.Reverse.from_handler(app)
        self.assertEqual(r.english.docs.news.item.as_url, '/item')

    def test_unicode(self):
        '''Routing rules with unicode'''
        # XXX move to urltemplate and reverse tests?
        app = web.cases(
            web.prefix(u'/հայերեն') | web.cases(
                web.match(u'/%', 'percent') | (lambda e,d: Response())
            )
        )
        encoded = '/%D5%B0%D5%A1%D5%B5%D5%A5%D6%80%D5%A5%D5%B6/%25'

        self.assertEqual(web.Reverse.from_handler(app).percent.as_url, encoded)
        self.assertEqual(web.Reverse.from_handler(app).percent.as_url.get_readable(), u'/հայերեն/%')

        self.assertNotEqual(web.ask(app, encoded), None)

        # ???
        # rctx have prefixes, so we need new one
        self.assertEqual(web.ask(app, encoded).status_int, 200)

    def test_prefix_with_zeros_in_int(self):
        '''Simple prefix'''

        def handler(env, data):
            return Response()

        app = web.cases(
            web.prefix('/section/<int:section_id>') | 
                web.match('/item', 'doc') |
                handler)

        #self.assertEqual(web.ask(app, '/section/1').status_int, 200)
        self.assertEqual(web.ask(app, '/section/1/item').status_int, 200)
        self.assertEqual(web.ask(app, '/section/001/item').status_int, 200)
        # XXX this test fails because of bug in prefix handler:
        # self.builder(**kwargs) - prefix is built from converted value and
        # contains no zeros


class Subdomain(unittest.TestCase):

    def test_subdomain(self):
        '''Subdomain filter'''

        def handler(env, data):
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
        app = web.subdomain(u'рф') | web.subdomain(u'сайт') | web.match('/', 'site') | (lambda e,d: Response() )
        encoded = 'http://xn--80aswg.xn--p1ai/'
        self.assertEqual(web.Reverse.from_handler(app).site.as_url.get_readable(), u'http://сайт.рф/')
        self.assertEqual(web.Reverse.from_handler(app).site.as_url, encoded)
        self.assertNotEqual(web.ask(app, encoded), None)


class Match(unittest.TestCase):

    def test_simple_match(self):
        '''Check simple case of match'''

        app = web.match('/first', 'first') | (lambda e,d: Response())

        self.assertEqual(web.ask(app, '/first').status_int, 200)
        self.assertEqual(web.ask(app, '/second'), None)

    def test_int_converter(self):
        '''Check int converter'''

        def handler(env, data):
            self.assertEqual(data.id, 42)
            return Response()

        app = web.cases(
            web.match('/first', 'first') | handler,
            web.match('/second/<int:id>', 'second') | handler)

        web.ask(app, '/second/42')

    def test_multiple_int_convs(self):
        '''Check multiple int converters'''

        def handler(env, data):
            self.assertEqual(data.id, 42)
            self.assertEqual(data.param, 23)
            return Response()

        app = web.cases(
            web.match('/first', 'first') | handler,
            web.match('/second/<int:id>/<int:param>', 'second') | handler)

        web.ask(app, '/second/42/23')

    def test_not_found(self):
        '''Check int converter with handler which accepts params'''

        def handler(env, data):
            return Response()

        app = web.cases(
            web.match('/first', 'first') | handler,
            web.match('/second/<int:id>', 'second') | handler)

        self.assert_(web.ask(app, '/second/42/') is None)
        self.assert_(web.ask(app, '/second/42s') is None)

    def test_sane_exceptions(self):
        # XXX what is this? 0_o
        'Not yet completed test of sane exceptions'
        @web.request_filter
        def get_items(env, data, nxt):
            return nxt(env, data)
        def raise_exc(env, data):
            raise Exception('somewhere deep inside')

        app = web.prefix('/prefix') | web.match('/', '') | get_items | raise_exc
        self.assertRaises(Exception, lambda: web.ask(app, '/prefix/'))

    def test_handler_after_case(self):
        '''Test if the handler next to cases is called'''

        r = Response()
        def handler(env, data):
            return r

        app = web.cases(
            web.match('/first', 'first'),
            web.match('/second/<int:id>', 'second')
        ) | handler

        self.assertEqual(web.ask(app, '/first'), r)
        self.assertEqual(web.ask(app, '/second/2'), r)


class Method(unittest.TestCase):

    def test_simple_match(self):
        '''Method'''
        from webob.exc import HTTPMethodNotAllowed

        app = web.cases(
                web.match('/', 'simple') | web.method('post'),
                web.match('/strict', 'strict') | web.method('post', strict=True)
            ) | (lambda e,d: Response())

        self.assertEqual(web.ask(app, '/'), None)
        self.assertEqual(web.ask(app, '/', method='post').status_int, 200)

        self.assertRaises(HTTPMethodNotAllowed, lambda: web.ask(app, '/strict').status_int)
        self.assertEqual(web.ask(app, '/strict', method='post').status_int, 200)


