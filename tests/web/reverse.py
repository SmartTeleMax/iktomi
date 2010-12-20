# -*- coding: utf-8 -*-

__all__ = ['ReverseTests']

import unittest
from insanities import web
from insanities.utils.storage import VersionedStorage


class ReverseTests(unittest.TestCase):

    def test_namespace(self):
        'Reverse namespace without env'
        self.assertEqual(web.Reverse({}).namespace, '')

    def test_namespace_from_env(self):
        'Reverse namespace from env'
        self.assertEqual(web.Reverse({}, env=VersionedStorage(namespace='ns')).namespace,
                         'ns')

    def test_one_handler(self):
        'Reverse one match'
        r = web.Reverse.from_handler(web.match('/', 'index'))
        self.assertEqual(str(r('index')), '/')

    def test_few_handlers(self):
        'Reverse a few handlers'
        chain = web.cases(
            web.match('/', 'index'),
            web.match('/docs', 'docs'),
            web.match('/news', 'news'),
            )
        r = web.Reverse.from_handler(chain)
        self.assertEqual(str(r('index')), '/')
        self.assertEqual(str(r('docs')), '/docs')
        self.assertEqual(str(r('news')), '/news')

    def test_error(self):
        'Reverse missing url name'
        self.assertRaises(KeyError, lambda: web.Reverse({})('missing'))

    def test_nested_cases(self):
        'Reverse with nested web.cases'
        chain = web.cases(
            web.cases(
                web.match('/', 'index'),
                web.match('/docs', 'docs'),
                web.cases(
                    web.match('/news', 'news'))))
        r = web.Reverse.from_handler(chain)
        self.assertEqual(str(r('index')), '/')
        self.assertEqual(str(r('docs')), '/docs')
        self.assertEqual(str(r('news')), '/news')

    def test_nested_cases_with_prefixes(self):
        'Reverse with nested web.cases with web.prefixes'
        chain = web.cases(
                web.match('/', 'index'),
                web.prefix('/docs') | web.cases(
                    web.match('/<int:id>', 'doc'),
                    web.match('/list', 'docs')),
                web.prefix('/news') | web.cases(
                    web.match('/<int:id>', 'news'),
                    web.match('/list', 'newslist')))

        r = web.Reverse.from_handler(chain)
        self.assertEqual(str(r('index')), '/')
        self.assertEqual(str(r('docs')), '/docs/list')
        self.assertEqual(str(r('newslist')), '/news/list')
        self.assertEqual(str(r('doc', id=1)), '/docs/1')
        self.assertEqual(str(r('news', id=1)), '/news/1')
