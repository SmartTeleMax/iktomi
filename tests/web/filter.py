# -*- coding: utf-8 -*-

__all__ = ['Prefix', 'Match', 'Subdomain']

import unittest
from iktomi import web
from webob import Response


class WebHandler(unittest.TestCase):

    def test_interface(self):
        self.assertRaises(NotImplementedError, web.WebHandler(), {}, {})

    def test_repr(self):
        # for coverage
        '%r' % web.WebHandler()
        '%r' % web.cases()
        '%r' % web.request_filter(lambda e, d, n: None)
        '%r' % web.match('/', 'index')
        '%r' % web.method('GET')
        '%r' % web.static_files('/prefix')
        '%r' % web.prefix('/prefix')
        '%r' % web.subdomain('name')
        '%r' % web.namespace('name')


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
        from iktomi.web.url_converters import Converter, ConvertError

        def handler(env, data):
            return Response()

        class ZeroInt(Converter):

            def to_python(self, value, env=None):
                try:
                    value = int(value)
                except ValueError:
                    raise ConvertError(self.name, value)
                else:
                    return value

            def to_url(self, value):
                return str(value)

        app = web.cases(
              web.prefix('/section/<int:section_id>',
                         convs={'int': ZeroInt}) |
                web.match('/item', 'doc') |
                handler)

        #self.assertEqual(web.ask(app, '/section/1').status_int, 200)
        self.assertEqual(web.ask(app, '/section/1/item').status_int, 200)
        self.assertEqual(web.ask(app, '/section/001/item').status_int, 200)
        # XXX this test fails because of bug in prefix handler:
        # self.builder(**kwargs) - prefix is built from converted value and
        # contains no zeros

    def test_match_empty_pattern(self):
        '''Test if prefix() works proper with empty patterns'''

        r = Response()
        app = web.prefix('') | web.match('/', 'index') | (lambda e,d: r)

        self.assertEqual(web.ask(app, '/'), r)


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

    def test_match_empty_pattern(self):
        '''Test if match() works proper with empty patterns'''

        r = Response()
        app = web.prefix('/') | web.match('', 'index') | (lambda e,d: r)

        self.assertEqual(web.ask(app, '/'), r)


class Method(unittest.TestCase):

    def test_head(self):
        handler = web.method('GET')
        self.assertEqual(handler._names, set(['GET', 'HEAD']))

    def test_simple_match(self):
        '''Method'''
        from webob.exc import HTTPMethodNotAllowed

        app = web.cases(
                web.match('/', 'simple') | web.method('post'),
                web.match('/second', 'second') | web.method('POST'),
                web.match('/strict', 'strict') | web.method('post', strict=True)
            ) | (lambda e,d: Response())

        self.assertEqual(web.ask(app, '/'), None)
        self.assertEqual(web.ask(app, '/', method='post').status_int, 200)
        self.assertEqual(web.ask(app, '/second', method='post').status_int, 200)

        self.assertRaises(HTTPMethodNotAllowed, lambda: web.ask(app, '/strict').status_int)
        self.assertEqual(web.ask(app, '/strict', method='post').status_int, 200)

    def test_by_method(self):
        app = web.match('/') | web.by_method({
            'DELETE': lambda e,d: Response('delete'),
            ('POST', 'PUT'): lambda e,d: Response('post'),
        })

        self.assertEqual(web.ask(app, '/', method="PUT").body, 'post')
        self.assertEqual(web.ask(app, '/', method="DELETE").body, 'delete')
        self.assertEqual(web.ask(app, '/').status_int, 405)


class Namespace(unittest.TestCase):

    def test_namespace_with_dot(self):
        app = web.cases(
                web.namespace("english.docs.news") | web.match('/item', 'item'),
                )
        r = web.Reverse.from_handler(app)
        self.assertEqual(r.english.docs.news.item.as_url, '/item')

    def test_nested_namespaces(self):
        def test_ns(env, data):
            self.assertEqual(env.namespace, 'ns1.ns2')
            return 1

        app = web.prefix('/ns1', name="ns1") | \
              web.prefix('/ns2', name="ns2") | \
              web.match() | test_ns

        self.assertEqual(web.ask(app, '/ns1/ns2'), 1)

    def test_empty(self):
        self.assertRaises(TypeError, web.namespace, '')

# XXX tests for static_files needed!
