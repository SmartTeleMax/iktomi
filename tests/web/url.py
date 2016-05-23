# -*- coding: utf-8 -*-

import unittest
import six
if six.PY2:
    from urllib import quote
else:
    from urllib.parse import quote

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
        self.assertIn(u, ['/path/to/something?title=title&id=3&page=5',
                          '/path/to/something?title=title&page=5&id=3',
                          '/path/to/something?id=3&page=5&title=title',
                          '/path/to/something?id=3&title=title&page=5',
                          '/path/to/something?page=5&id=3&title=title',
                          '/path/to/something?page=5&title=title&id=3',])

    def test_param_set(self):
        'Set new param in url'
        u = URL('/path/to/something', query=[('title', 'title'), ('id', 3), ('page', 5)])
        self.assertEqual(u, '/path/to/something?title=title&id=3&page=5')
        if six.PY2:
            u = u.qs_set(page=long(2))
            self.assertEqual(u, '/path/to/something?title=title&id=3&page=2')
        u = u.qs_set(page=6)
        self.assertEqual(u, '/path/to/something?title=title&id=3&page=6')
        u = u.qs_set(page=7, title='land')
        self.assertIn(u, ['/path/to/something?id=3&page=7&title=land',
                          '/path/to/something?id=3&title=land&page=7'])

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
        self.assertIn(url.qs_set(a=1, b=2), ['/?a=1&b=2',
                                             '/?b=2&a=1'])
        url = url.qs_set([('a', '1'), ('a', '2'), ('b', '3')])
        self.assertEqual(url, '/?a=1&a=2&b=3')
        self.assertEqual(url.qs_set([('a', '1'), ('c', '2')]), '/?b=3&a=1&c=2')
        self.assertRaises(TypeError, url.qs_set, [('a', 1)], z=0)

    def test_param_add_args(self):
        'Add param to url'
        url = URL('/')
        self.assertIn(url.qs_add([('a', 1), ('c', 3)], a=2, b=2),
                        ['/?a=1&c=3&a=2&b=2',
                         '/?a=1&c=3&b=2&a=2'])

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

    #def test_quote(self):
    #    # XXX this is WRONG!
    #    # We shold not try to unquote the urlqouted values!
    #    # Otherwise it is impossible to build a consistent interface
    #    # If you want magic - use URL.from_url method!
    #    u = URL(quote('/path/to/+'))
    #    self.assertEqual(u, '/path/to/%2B')
    #    u = u.qs_set(page=7)
    #    self.assertEqual(u, '/path/to/%2B?page=7')

    def test_iri(self):
        u = URL('/', host=u'example.com')
        self.assertEqual(u, u'http://example.com/')
        u = URL(u'/урл/', host=u'сайт.рф', query={'q': u'поиск'}, fragment=u"якорь")
        self.assertEqual(u, u'http://xn--80aswg.xn--p1ai'
                                    u'/%D1%83%D1%80%D0%BB/'
                                    u'?q=%D0%BF%D0%BE%D0%B8%D1%81%D0%BA'
                                    u'#%D1%8F%D0%BA%D0%BE%D1%80%D1%8C')
        # Note: you should probably not use unicode in fragment part of URL.
        #       We encode it according to RFC, but different client handle
        #       it in different ways: Chrome allows unicode and does not 
        #       encode/decode it at all, while Firefox handles it according RFC

    def test_no_quote(self):
        u = URL(u'/урл/', host=u'сайт.рф', query={'q': u'поиск'}, fragment=u"якорь")
        self.assertEqual(u.get_readable(), u'http://сайт.рф/урл/?q=поиск#якорь')

    def test_quotted_path_to_constructor(self):
        u = URL(u'/%D1%83/',
                host=u'xn--80aswg.xn--p1ai',
                query={'q': u'%D0%BF'},
                fragment=u"%D1%8F")
        # We shold not try to unquote the urlqouted values!
        # Otherwise it is impossible to build a consistent interface
        self.assertEqual(u, u'http://xn--80aswg.xn--p1ai/%25D1%2583/?q=%25D0%25BF#%25D1%258F')
        self.assertEqual(u.get_readable(), u'http://сайт.рф/%D1%83/?q=%D0%BF#%D1%8F')

    def test_from_url(self):
        url = URL.from_url('http://example.com/url?a=1&b=2&b=3#anchor', show_host=False)
        self.assertEqual(url.schema, 'http')
        self.assertEqual(url.host, 'example.com')
        self.assertEqual(url.port, '')
        self.assertEqual(url.path, '/url')
        self.assertEqual(url.fragment, 'anchor')
        self.assertEqual(set(url.query.items()), {('a' ,'1'), ('b', '2'), ('b', '3')})
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
        self.assertEqual(set(url.query.items()), {('a' ,'1'), ('b', '2'), ('b', '3')})

    def test_from_url_idna(self):
        src = (u'http://xn--80aswg.xn--p1ai'
                                u'/%D1%83%D1%80%D0%BB/'
                                u'?q=%D0%BF%D0%BE%D0%B8%D1%81%D0%BA'
                                u'#%D1%8F%D0%BA%D0%BE%D1%80%D1%8C')

        url = URL.from_url(src.encode('utf-8'))
        self.assertEqual(url.get_readable(),
                         u'http://сайт.рф/урл/?q=поиск#якорь')

        url = URL.from_url(src)
        self.assertEqual(url.get_readable(),
                         u'http://сайт.рф/урл/?q=поиск#якорь')

    def test_from_url_broken_unicode(self):
        url = URL.from_url('/search%E3%81?q=hello%E3%81#hash%E3%81')
        self.assertEqual(url.get_readable(),
                         u'/search�?q=hello�#hash�')

    def test_cyrillic_path(self):
        url1 = URL.from_url(u'http://test.ru/тест'.encode('utf-8')) # encoded unicode
        url2 = URL.from_url(u'http://test.ru/тест') # decoded unicode
        # should work both without errors
        self.assertEqual(url1.path, '/%D1%82%D0%B5%D1%81%D1%82')
        self.assertEqual(url1.path, url2.path)

    def test_empty_fragment(self):
        # XXX is this a good interface?
        self.assertEqual(URL.from_url('/').fragment, None)
        self.assertEqual(URL.from_url('/#').fragment, '')

        self.assertEqual(URL('/', fragment=None), '/')
        self.assertEqual(URL('/', fragment='') ,'/#')


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

    def test_parse_cp_1251(self):
        url_string = u"http://test.com/?query=привет".encode('cp1251')
        url = URL.from_url(url_string)
        self.assertEqual(url.host, 'test.com')
        self.assertEqual(url.query['query'], u'�'*6)

