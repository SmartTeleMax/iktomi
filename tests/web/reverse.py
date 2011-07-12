# -*- coding: utf-8 -*-

__all__ = ['ReverseTests', 'LocationsTests']

import unittest
from insanities import web
from insanities.utils.storage import VersionedStorage
from insanities.web.url import UrlTemplate
from insanities.web.reverse import Location, UrlBuildingError


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
        self.assert_(web.locations(chain)['index'][0].builders)
        self.assertEqual(len(web.locations(chain)['index'][0].builders), 2)

    def test_prefix_and_cases(self):
        'Locations of web.cases with prefix'
        chain = web.prefix('/news') | web.cases(
                web.match('/', 'index'),
                web.match('/docs', 'docs'))
        for k in ('index', 'docs'):
            self.assert_(web.locations(chain).keys(), [k])
            self.assert_(web.locations(chain)[k][0].builders)
            self.assertEqual(len(web.locations(chain)[k][0].builders), 2)

    def test_namespace(self):
        'Locations namespace'
        chain = web.namespace('news') | web.match('/', 'index')
        self.assert_(web.locations(chain).keys(), ['news.index'])

    def test_namespace_and_cases(self):
        'Locations namespace with web.cases'
        chain = web.namespace('news') | web.cases(
                web.match('/', 'index'),
                web.match('/docs', 'docs'))
        self.assertEqual(web.locations(chain).keys(), ['news'])
        self.assertEqual(web.locations(chain)['news'][1].keys(), ['index', 'docs'])

    def test_mix(self):
        'Loactions mix'
        chain = web.prefix('/items') | web.cases(
            web.match('/', 'index'),
            web.prefix('/news') | web.namespace('news') | web.cases(
                web.match('/'),
                web.match('/<int:id>', 'item'),
                web.prefix('/docs') | web.namespace('docs') | web.cases(
                    web.match('/'),
                    web.match('/<int:id>', 'item'))))
        locations = web.locations(chain)
        self.assertEqual(locations.keys(), ['index', 'news'])
        self.assertEqual(locations['index'][0], 
                         Location(*(UrlTemplate('/items', match_whole_str=False), UrlTemplate('/'))))
        self.assertEqual(locations['news'][0], 
                         Location(*(UrlTemplate('/items', match_whole_str=False), UrlTemplate('/news', match_whole_str=False))))
        self.assertEqual(locations['news'][1][''][0], Location(UrlTemplate('/')))
        self.assertEqual(locations['news'][1]['item'][0], Location(UrlTemplate('/<int:id>')))
        self.assertEqual(locations['news'][1]['docs'][0], 
                         Location(UrlTemplate('/docs', match_whole_str=False)))
        self.assertEqual(locations['news'][1]['docs'][1][''][0], Location(UrlTemplate('/')))
        self.assertEqual(locations['news'][1]['docs'][1]['item'][0], Location(UrlTemplate('/<int:id>')))

    def test_namespace_with_empty_name(self):
        'Namespaces with empty url name'
        chain = web.namespace('news') | web.match('/')
        self.assert_(web.locations(chain).keys(), ['news'])

    def test_subdomain(self):
        'Locations and subdomains'
        chain = web.subdomain('news') | web.match('/', 'index')
        self.assert_(web.locations(chain).keys(), ['index'])
        self.assert_(web.locations(chain)['index'][0].subdomains)
        self.assertEqual(web.locations(chain)['index'][0].subdomains, 
                         ['news'])

    def test_subdomains_and_cases(self):
        'Locations of web.cases with subdomains'
        chain = web.subdomain('news') | web.cases(
                web.match('/', 'index'),
                web.match('/docs', 'docs'))
        for k in ('index', 'docs'):
            self.assert_(web.locations(chain).keys(), [k])
            self.assert_(web.locations(chain)[k][0].subdomains)
            self.assertEqual(web.locations(chain)[k][0].subdomains,
                             ['news'])


class ReverseTests(unittest.TestCase):

    def test_one_handler(self):
        'Reverse one match'
        r = web.Reverse.from_handler(web.match('/', 'index'))
        self.assertEqual(r.index.as_url, '/')

    def test_few_handlers(self):
        'Reverse a few handlers'
        chain = web.cases(
            web.match('/', 'index'),
            web.match('/docs', 'docs'),
            web.match('/news', 'news'),
            )
        r = web.Reverse.from_handler(chain)
        self.assertEqual(r.index.as_url, '/')
        self.assertEqual(r.docs.as_url, '/docs')
        self.assertEqual(r.news.as_url, '/news')

    def test_nested_cases(self):
        'Reverse with nested web.cases'
        chain = web.cases(
            web.cases(
                web.match('/', 'index'),
                web.match('/docs', 'docs'),
                web.cases(
                    web.match('/news', 'news'))))
        r = web.Reverse.from_handler(chain)
        self.assertEqual(r.index.as_url, '/')
        self.assertEqual(r.docs.as_url, '/docs')
        self.assertEqual(r.news.as_url, '/news')

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
        self.assertEqual(r.index.as_url, '/')
        self.assertEqual(r.docs.as_url, '/docs/list')
        self.assertEqual(r.newslist.as_url, '/news/list')
        self.assertEqual(r.doc(id=1).as_url, '/docs/1')
        self.assertEqual(r.news(id=1).as_url, '/news/1')

    def test_unicode(self):
        'Reverse with unicode'
        # various combinations of url parts containing unicode
        chain = web.subdomain(u'п') | web.cases(
            web.prefix(u'/з') | web.match('/', 'unicode1'),
            web.prefix(u'/з') | web.match('/<string:slug>', 'unicode2'),
            web.match(u'/д/<string:slug>', 'unicode3'), #regression
            web.match(u'/<string:slug1>/<string:slug2>', 'unicode4'), #regression
        )
        r = web.Reverse.from_handler(chain)

        self.assertEqual(r.unicode1.as_url, 'http://xn--o1a/%D0%B7/')
        self.assertEqual(r.unicode2(slug=u'ю').as_url, 'http://xn--o1a/%D0%B7/%D1%8E')
        self.assertEqual(r.unicode3(slug=u'ю').as_url, 'http://xn--o1a/%D0%B4/%D1%8E')
        self.assertEqual(r.unicode4(slug1=u'д', slug2=u'ю').as_url, 'http://xn--o1a/%D0%B4/%D1%8E')

    def test_nested_prefixes(self):
        'Reverse with nested prefexes'
        app = web.prefix('/news/<section>') | web.namespace('news') | web.cases(
                web.match(),
                web.prefix('/<int:id>') | web.namespace('item') | web.cases(
                    web.match(),
                    web.prefix('/docs') | web.namespace('docs') | web.cases(
                        web.match(),
                        web.match('/<int:id>', 'item'))))
        r = web.Reverse.from_handler(app)

        # Normal behavior
        self.assertEqual(r.news(section='top').as_url, '/news/top')
        self.assertEqual(r.news(section='top').item(id=1).as_url, '/news/top/1')
        self.assertEqual(r.news(section='top').item(id=1).docs.as_url, '/news/top/1/docs')
        self.assertEqual(r.news(section='top').item(id=1).docs.item(id=2).as_url, '/news/top/1/docs/2')

        # Exceptional behavior
        self.assertRaises(UrlBuildingError, lambda: r.news.as_url)
        self.assertRaises(UrlBuildingError, lambda: r.news(section='top').item.as_url)
        self.assertRaises(UrlBuildingError, lambda: r.news(section='top').item(id=1).docs())
        self.assertRaises(UrlBuildingError, lambda: r.news.item)
