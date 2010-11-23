# -*- coding: utf-8 -*-

import unittest
from urllib import quote
from insanities.web.url import URL, UrlTemplate


class URLTests(unittest.TestCase):

    def test_rendering_without_params(self):
        'Url without params'
        u = URL('/path/to/something')
        self.assertEqual(str(u), '/path/to/something')

    def test_rendering_with_params(self):
        'Url with params'
        u = URL('/path/to/something', query=dict(id=3, page=5, title='title'))
        self.assertEqual(str(u), '/path/to/something?title=title&id=3&page=5')

    def test_param_set(self):
        'Set new param in url'
        u = URL('/path/to/something', query=dict(id=3, page=5, title='title'))
        self.assertEqual(str(u), '/path/to/something?title=title&id=3&page=5')
        u = u.set(page=6)
        self.assertEqual(str(u), '/path/to/something?title=title&id=3&page=6')
        u = u.set(page=7, title='land')
        self.assertEqual(str(u), '/path/to/something?id=3&page=7&title=land')

    def test_param_get(self):
        'Get param from url'
        u = URL('/path/to/something', query=dict(id=3, page=5, title='title'))
        page = u.get('page')
        self.assertEqual(page, 5)
        u = u.set(page=7)
        page = u.get('page')
        self.assertEqual(page, 7)
        not_here = u.get('not_here')
        self.assertEqual(not_here, None)

    def test_quote(self):
        u = URL(quote('/path/to/+'))
        self.assertEqual(str(u), '/path/to/%2B')
        u = u.set(page=7)
        self.assertEqual(str(u), '/path/to/%2B?page=7')

    def test_iri(self):
        u = URL('/', host=u'example.com')
        self.assertEqual(str(u), u'http://example.com/')
        u = URL(u'/урл/', host=u'сайт.рф', query={'q': u'поиск'})
        self.assertEqual(str(u), u'http://xn--80aswg.xn--p1ai/%D1%83%D1%80%D0%BB/?q=%D0%BF%D0%BE%D0%B8%D1%81%D0%BA')

    def test_no_quote(self):
        u = URL(u'/урл/', host=u'сайт.рф', query={'q': u'поиск'})
        self.assertEqual(u.get_readable(), u'http://сайт.рф/урл/?q=поиск')


class UrlTemplateTest(unittest.TestCase):
    def test_match(self):
        'Simple match'
        t = UrlTemplate('/')
        self.assertEqual(t.match('/'), (True, {}))

    def test_static_text(self):
        'Simple text match'
        t = UrlTemplate('/test/url')
        self.assertEqual(t.match('/test/url'), (True, {}))

    def test_converter(self):
        'Simple text match'
        t = UrlTemplate('/<string:name>')
        self.assertEqual(t.match('/somevalue'), (True, {'name': 'somevalue'}))

    def test_default_converter(self):
        'Default converter test'
        t = UrlTemplate('/<name>')
        self.assertEqual(t.match('/somevalue'), (True, {'name': 'somevalue'}))

    def test_multiple_converters(self):
        'Multiple converters'
        t = UrlTemplate('/<name>/text/<action>')
        self.assertEqual(t.match(quote('/this/text/edit')), (True, {'name': 'this', 'action': 'edit'}))

    def test_multiple_converters_postfix(self):
        'Multiple converters with postfix data'
        t = UrlTemplate('/<name>/text/<action>/post')
        self.assertEqual(t.match(quote(u'/this/text/edit/post')), (True, {'name': 'this', 'action': 'edit'}))
        self.assertEqual(t.match(quote(u'/this/text/edit')), (False, {}))

    def test_unicode(self):
        'Unicode values of converters'
        t = UrlTemplate('/<name>/text/<action>')
        self.assertEqual(t.match(quote(u'/имя/text/действие'.encode('utf-8'))), (True, {'name': u'имя', 'action': u'действие'}))
