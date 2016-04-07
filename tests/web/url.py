# -*- coding: utf-8 -*-

import unittest
from urllib import quote
from iktomi.web.reverse import URL
from iktomi.web.url_templates import UrlTemplate
from iktomi.web.url_converters import Converter, ConvertError


class URLTests(unittest.TestCase):

    def test_rendering_without_params(self):
        'Url without params'
        u = URL('/path/to/something')
        self.assertEqual(u, '/path/to/something')
        self.assert_(u in repr(u))

    def test_rendering_with_params(self):
        'Url with params'
        u = URL('/path/to/something', query=dict(id=3, page=5, title='title'))
        self.assertEqual(u, '/path/to/something?title=title&id=3&page=5')

    def test_param_set(self):
        'Set new param in url'
        u = URL('/path/to/something', query=dict(id=3, page=5, title='title'))
        self.assertEqual(u, '/path/to/something?title=title&id=3&page=5')
        u = u.qs_set(page=6)
        self.assertEqual(u, '/path/to/something?title=title&id=3&page=6')
        u = u.qs_set(page=7, title='land')
        self.assertEqual(u, '/path/to/something?id=3&page=7&title=land')

    def test_param_delete(self):
        'Set new param in url'
        u = URL('/path/to/something', query=[('id', 3), ('page', 5), ('page', 6)])
        self.assertEqual(u, '/path/to/something?id=3&page=5&page=6')
        u = u.qs_delete('page')
        self.assertEqual(u, '/path/to/something?id=3')
        u = u.qs_delete('offset')
        self.assertEqual(u, '/path/to/something?id=3')

    def test_params_set_args(self):
        'Use multidict to set params in url'
        url = URL('/')
        self.assertEqual(url.qs_set(a=1, b=2), '/?a=1&b=2')
        url = url.qs_set([('a', '1'), ('a', '2'), ('b', '3')])
        self.assertEqual(url, '/?a=1&a=2&b=3')
        self.assertEqual(url.qs_set([('a', '1'), ('c', '2')]), '/?b=3&a=1&c=2')
        self.assertRaises(TypeError, url.qs_set, [('a', 1)], z=0)

    def test_param_add_args(self):
        'Add param to url'
        url = URL('/')
        self.assertEqual(url.qs_add([('a', 1), ('c', 3)], a=2, b=2), '/?a=1&c=3&a=2&b=2')

    def test_param_get(self):
        'Get param from url'
        u = URL('/path/to/something', query=dict(id=3, page=5, title='title'))
        page = u.qs_get('page')
        self.assertEqual(page, 5)
        u = u.qs_set(page=7)
        page = u.qs_get('page')
        self.assertEqual(page, 7)
        not_here = u.qs_get('not_here')
        self.assertEqual(not_here, None)

    def test_quote(self):
        u = URL(quote('/path/to/+'))
        self.assertEqual(u, '/path/to/%2B')
        u = u.qs_set(page=7)
        self.assertEqual(u, '/path/to/%2B?page=7')

    def test_iri(self):
        u = URL('/', host=u'example.com')
        self.assertEqual(u, u'http://example.com/')
        u = URL(u'/урл/', host=u'сайт.рф', query={'q': u'поиск'})
        self.assertEqual(u, u'http://xn--80aswg.xn--p1ai/%D1%83%D1%80%D0%BB/?q=%D0%BF%D0%BE%D0%B8%D1%81%D0%BA')

    def test_no_quote(self):
        u = URL(u'/урл/', host=u'сайт.рф', query={'q': u'поиск'})
        self.assertEqual(u.get_readable(), u'http://сайт.рф/урл/?q=поиск')

    def test_from_url(self):
        url = URL.from_url('http://example.com/url?a=1&b=2&b=3', show_host=False)
        self.assertEqual(url.schema, 'http')
        self.assertEqual(url.host, 'example.com')
        self.assertEqual(url.port, '')
        self.assertEqual(url.path, '/url')
        self.assertEqual(url.query.items(), [('a' ,'1'), ('b', '2'), ('b', '3')])
        self.assertEqual(url.show_host, False)

    def test_from_url_unicode(self):
        url = URL.from_url(u'http://сайт.рф/', show_host=False)
        self.assertEqual(url.schema, 'http')
        self.assertEqual(url.host, u'сайт.рф')
        self.assertEqual(url.port, '')
        self.assertEqual(url.path, '/')
        self.assertEqual(url.show_host, False)

    def test_from_url_path(self):
        url = URL.from_url('/url?a=1&b=2&b=3')
        self.assertEqual(url.schema, 'http')
        self.assertEqual(url.host, '')
        self.assertEqual(url.port, '')
        self.assertEqual(url.path, '/url')
        self.assertEqual(url.query.items(), [('a' ,'1'), ('b', '2'), ('b', '3')])

    def test_from_url_idna(self):
        url = URL.from_url('http://xn--80aswg.xn--p1ai/%D1%83%D1%80%D0%BB/?q=%D0%BF%D0%BE%D0%B8%D1%81%D0%BA')
        self.assertEqual(url.get_readable(),
                         u'http://сайт.рф/урл/?q=поиск')

    def test_from_url_broken_unicode(self):
        url = URL.from_url('/search?q=hello%E3%81')
        self.assertEqual(url.get_readable(),
                         u'/search?q=hello�')

    def test_cyrillic_path(self):
        url1 = URL.from_url('http://test.ru/тест') # encoded unicode
        url2 = URL.from_url(u'http://test.ru/тест') # decoded unicode
        # should work both without errors
        self.assertEqual(url1.path, '/%D1%82%D0%B5%D1%81%D1%82')
        self.assertEqual(url1.path, url2.path)

class UrlTemplateTest(unittest.TestCase):
    def test_match(self):
        'Simple match'
        t = UrlTemplate('/')
        self.assertEqual(t.match('/'), ('/', {}))

    def test_static_text(self):
        'Simple text match'
        t = UrlTemplate('/test/url')
        self.assertEqual(t.match('/test/url'), ('/test/url', {}))

    def test_converter(self):
        'Simple text match'
        t = UrlTemplate('/<string:name>')
        self.assertEqual(t.match('/somevalue'), ('/somevalue', {'name': 'somevalue'}))

    def test_default_converter(self):
        'Default converter test'
        t = UrlTemplate('/<name>')
        self.assertEqual(t.match('/somevalue'), ('/somevalue', {'name': 'somevalue'}))

    def test_multiple_converters(self):
        'Multiple converters'
        t = UrlTemplate('/<name>/text/<action>')
        self.assertEqual(t.match('/this/text/edit'), ('/this/text/edit', {'name': 'this', 'action': 'edit'}))

    def test_multiple_converters_postfix(self):
        'Multiple converters with postfix data'
        t = UrlTemplate('/<name>/text/<action>/post')
        self.assertEqual(t.match('/this/text/edit/post'), ('/this/text/edit/post', {'name': 'this', 'action': 'edit'}))
        self.assertEqual(t.match('/this/text/edit'), (None, {}))

    def test_unicode(self):
        'Unicode values of converters'
        t = UrlTemplate('/<name>/text/<action>')
        url = quote(u'/имя/text/действие'.encode('utf-8'))
        self.assertEqual(t.match(url), (url, {'name': u'имя', 'action': u'действие'}))

    def test_incorrect_value(self):
        'Incorrect url encoded value'
        t = UrlTemplate('/<name>')
        value = quote(u'/имя'.encode('utf-8'))[:-1]
        self.assertEqual(t.match(value), (value, {'name': u'\u0438\u043c\ufffd%8'}))

    def test_incorrect_urlencoded_path(self):
        'Incorrect url encoded path'
        t = UrlTemplate('/<name>')
        value = quote(u'/имя'.encode('utf-8'))+'%r1'
        self.assertEqual(t.match(value), (value, {'name': u'\u0438\u043c\u044f%r1'}))

    def test_converter_with_args(self):
        'Converter with args'
        class Conv(Converter):
            def __init__(self, *items):
                self.items = items
            def to_python(self, value, **kw):
                if value not in self.items:
                    raise ConvertError(self, value)
                return value
        t = UrlTemplate(u'/<conv(u"text", u"тест", noquote):name>',
                        converters={'conv': Conv})
        value = quote(u'/имя'.encode('utf-8'))
        self.assertEqual(t.match(value), (None, {}))
        value = quote(u'/text'.encode('utf-8'))
        self.assertEqual(t.match(value), (value, {'name': u'text'}))
        value = quote(u'/тест'.encode('utf-8'))
        self.assertEqual(t.match(value), (value, {'name': u'тест'}))
        value = quote(u'/noquote'.encode('utf-8'))
        self.assertEqual(t.match(value), (value, {'name': u'noquote'}))

    def test_incorrect_url_template(self):
        'Incorrect url template'
        self.assertRaises(ValueError, lambda: UrlTemplate('/<name></'))

    def test_incorrect_url_template1(self):
        'Incorrect url template 1'
        self.assertRaises(ValueError, lambda: UrlTemplate('/<:name>/'))

    def test_unknown_converter(self):
        'Unknown converter'
        self.assertRaises(KeyError, lambda: UrlTemplate('/<baba:name>/'))
        self.assertRaises(KeyError, lambda: UrlTemplate('/<baba:name></'))
