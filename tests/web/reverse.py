# -*- coding: utf-8 -*-

__all__ = ['ReverseTests', 'LocationsTests']

import unittest
from insanities import web
from insanities.utils.storage import VersionedStorage


class LocationsTests(unittest.TestCase):

    def test_match(self):
        'Locations of web.match'
        self.assert_(web.locations(web.match('/', 'name')).keys(), ['name'])

    def test_match_dublication(self):
        'Raise error on same url names'
        self.assertRaises(ValueError, lambda: web.locations(
                web.cases(
                    web.match('/', 'index'),
                    web.match('/index', 'index'))))

    def test_cases(self):
        'Locations of web.cases'
        chain = web.cases(
                web.match('/', 'index'),
                web.match('/docs', 'docs'))
        self.assert_(web.locations(chain).keys(), ['index', 'docs'])

    def test_nested_cases(self):
        'Locations of nested web.cases'
        chain = web.cases(
                web.match('/', 'index'),
                web.cases(
                    web.match('/docs', 'docs')))
        self.assert_(web.locations(chain).keys(), ['index', 'docs'])

    def test_prefix(self):
        'Locations of web.match with prefix'
        chain = web.prefix('/news') | web.match('/', 'index')
        self.assert_(web.locations(chain).keys(), ['index'])
        self.assert_('builders' in web.locations(chain)['index'])
        self.assertEqual(len(web.locations(chain)['index']['builders']), 2)

    def test_prefix_and_cases(self):
        'Locations of web.cases with prefix'
        chain = web.prefix('/news') | web.cases(
                web.match('/', 'index'),
                web.match('/docs', 'docs'))
        for k in ('index', 'docs'):
            self.assert_(web.locations(chain).keys(), [k])
            self.assert_('builders' in web.locations(chain)[k])
            self.assertEqual(len(web.locations(chain)[k]['builders']), 2)

    def test_namespace(self):
        'Locations namespace'
        chain = web.namespace('news') | web.match('/', 'index')
        self.assert_(web.locations(chain).keys(), ['news.index'])

    def test_namespace_and_cases(self):
        'Locations namespace with web.cases'
        chain = web.namespace('news') | web.cases(
                web.match('/', 'index'),
                web.match('/docs', 'docs'))
        self.assertEqual(web.locations(chain).keys(), ['news.index', 'news.docs'])

    def test_mix(self):
        'Loactions mix'
        chain = web.prefix('/items') | web.cases(
            web.match('/', 'index'),
            web.prefix('/news') | web.namespace('news') | web.cases(
                web.match('/', 'index'),
                web.match('/<int:id>', 'item')),
            web.prefix('/docs') | web.namespace('docs') | web.cases(
                web.match('/', 'index'),
                web.match('/<int:id>', 'item')))
        locations = web.locations(chain)
        self.assertEqual(locations.keys(), 
                         ['index', 'docs.index', 'docs.item',
                          'news.item', 'news.index'])
        self.assertEqual(len(locations['index']['builders']), 2)
        self.assertEqual(len(locations['news.index']['builders']), 3)
        self.assertEqual(len(locations['news.item']['builders']), 3)
        self.assertEqual(len(locations['docs.index']['builders']), 3)
        self.assertEqual(len(locations['docs.item']['builders']), 3)

    def test_namespace_with_empty_name(self):
        'Namespaces with empty url name'
        chain = web.namespace('news') | web.match('/', '')
        self.assert_(web.locations(chain).keys(), ['news'])

    def test_subdomain(self):
        'Locations and subdomains'
        chain = web.subdomain('news') | web.match('/', 'index')
        self.assert_(web.locations(chain).keys(), ['index'])
        self.assert_('subdomains' in web.locations(chain)['index'])
        self.assertEqual(web.locations(chain)['index']['subdomains'], 
                         ['news'])

    def test_subdomains_and_cases(self):
        'Locations of web.cases with subdomains'
        chain = web.subdomain('news') | web.cases(
                web.match('/', 'index'),
                web.match('/docs', 'docs'))
        for k in ('index', 'docs'):
            self.assert_(web.locations(chain).keys(), [k])
            self.assert_('subdomains' in web.locations(chain)[k])
            self.assertEqual(web.locations(chain)[k]['subdomains'],
                             ['news'])


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
        self.assertEqual(r('index'), '/')

    def test_few_handlers(self):
        'Reverse a few handlers'
        chain = web.cases(
            web.match('/', 'index'),
            web.match('/docs', 'docs'),
            web.match('/news', 'news'),
            )
        r = web.Reverse.from_handler(chain)
        self.assertEqual(r('index'), '/')
        self.assertEqual(r('docs'), '/docs')
        self.assertEqual(r('news'), '/news')

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
        self.assertEqual(r('index'), '/')
        self.assertEqual(r('docs'), '/docs')
        self.assertEqual(r('news'), '/news')

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
        self.assertEqual(r('index'), '/')
        self.assertEqual(r('docs'), '/docs/list')
        self.assertEqual(r('newslist'), '/news/list')
        self.assertEqual(r('doc', id=1), '/docs/1')
        self.assertEqual(r('news', id=1), '/news/1')

    def test_unicode(self):
        'Reverse with unicode'
        handler = web.match('/doc/<string:slug>', 'doc')
        r = web.Reverse.from_handler(handler)
        self.assertEqual(r('doc', slug=u'ю'), '/doc/%D1%8E')


