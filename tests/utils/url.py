# -*- coding: utf-8 -*-

import unittest
from insanities.utils.url import URL


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
        u = URL('/path/to/+')
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

