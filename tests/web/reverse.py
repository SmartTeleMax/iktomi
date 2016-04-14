# -*- coding: utf-8 -*-

__all__ = ['ReverseTests', 'LocationsTests']

import unittest
from webob import Response
from iktomi import web
from iktomi.web.url_templates import UrlTemplate
from iktomi.web.reverse import Location, UrlBuildingError


def locations(handler):
    return handler._locations()


class LocationsTests(unittest.TestCase):

    def test_repr(self):
        # for coverage
        "%r" % Location(UrlTemplate('/docs', match_whole_str=False))

    def test_match(self):
        'Locations of web.match'
        self.assert_(locations(web.match('/', 'name')).keys(), ['name'])

    def test_match_dublication(self):
        'Raise error on same url names'
        self.assertRaises(ValueError, lambda: locations(
                web.cases(
                    web.match('/', 'index'),
                    web.match('/index', 'index'))))

    def test_cases(self):
        'Locations of web.cases'
        chain = web.cases(
                web.match('/', 'index'),
                web.match('/docs', 'docs'))
        self.assert_(locations(chain).keys(), ['index', 'docs'])

    def test_nested_cases(self):
        'Locations of nested web.cases'
        chain = web.cases(
                web.match('/', 'index'),
                web.cases(
                    web.match('/docs', 'docs')))
        self.assert_(locations(chain).keys(), ['index', 'docs'])

    def test_prefix(self):
        'Locations of web.match with prefix'
        chain = web.prefix('/news') | web.match('/', 'index')
        self.assert_(locations(chain).keys(), ['index'])
        self.assert_(locations(chain)['index'][0].builders)
        self.assertEqual(len(locations(chain)['index'][0].builders), 2)

    def test_prefix_and_cases(self):
        'Locations of web.cases with prefix'
        chain = web.prefix('/news') | web.cases(
                web.match('/', 'index'),
                web.match('/docs', 'docs'))
        for k in ('index', 'docs'):
            self.assert_(locations(chain).keys(), [k])
            self.assert_(locations(chain)[k][0].builders)
            self.assertEqual(len(locations(chain)[k][0].builders), 2)

    def test_namespace(self):
        'Locations namespace'
        chain = web.namespace('news') | web.match('/', 'index')
        self.assert_(locations(chain).keys(), ['news.index'])

    def test_namespace_and_cases(self):
        'Locations namespace with web.cases'
        chain = web.namespace('news') | web.cases(
                web.match('/', 'index'),
                web.match('/docs', 'docs'))
        self.assertEqual(locations(chain).keys(), ['news'])
        self.assertEqual(locations(chain)['news'][1].keys(), ['index', 'docs'])

    def test_mix(self):
        'Loactions mix'
        chain = web.prefix('/items') | web.cases(
            web.match('/'),
            web.prefix('/news') | web.namespace('news') | web.cases(
                web.match('/'),
                web.match('/<int:id>', 'item'),
                web.prefix('/docs') | web.namespace('docs') | web.cases(
                    web.match('/'),
                    web.match('/<int:id>', 'item'))))
        locs = locations(chain)
        self.assertEqual(locs.keys(), ['', 'news'])
        self.assertEqual(locs[''][0], 
                         Location(*(UrlTemplate('/items', match_whole_str=False), UrlTemplate('/'))))
        self.assertEqual(locs['news'][0], 
                         Location(*(UrlTemplate('/items', match_whole_str=False), UrlTemplate('/news', match_whole_str=False))))
        self.assertEqual(locs['news'][1][''][0], Location(UrlTemplate('/')))
        self.assertEqual(locs['news'][1]['item'][0], Location(UrlTemplate('/<int:id>')))
        self.assertEqual(locs['news'][1]['docs'][0], 
                         Location(UrlTemplate('/docs', match_whole_str=False)))
        self.assertEqual(locs['news'][1]['docs'][1][''][0], Location(UrlTemplate('/')))
        self.assertEqual(locs['news'][1]['docs'][1]['item'][0], Location(UrlTemplate('/<int:id>')))

    def test_namespace_with_empty_name(self):
        'Namespaces with empty url name'
        chain = web.namespace('news') | web.match('/')
        self.assert_(locations(chain).keys(), ['news'])

    def test_subdomain(self):
        'Locations and subdomains'
        chain = web.subdomain('news') | web.match('/', 'index')
        self.assert_(locations(chain).keys(), ['index'])
        self.assert_(locations(chain)['index'][0].subdomains)

        subdomains = [x.primary 
                      for x in locations(chain)['index'][0].subdomains]
        self.assertEqual(subdomains, ['news'])

    def test_subdomains_and_cases(self):
        'Locations of web.cases with subdomains'
        chain = web.subdomain('news') | web.cases(
                web.match('/', 'index'),
                web.match('/docs', 'docs'))
        for k in ('index', 'docs'):
            self.assert_(locations(chain).keys(), [k])
            self.assert_(locations(chain)[k][0].subdomains)
            subdomains = [x.primary 
                      for x in locations(chain)[k][0].subdomains]
            self.assertEqual(subdomains, ['news'])

    def test_function(self):
        'Reverse working with chained functions'
        app = web.cases(
            web.match('/', 'index') | (lambda e, d: None),
            web.prefix('/xx') | (lambda e, d: None),
            (lambda e, d: None),
        )
        self.assertEqual(locations(app).keys(), ['index'])


class ReverseTests(unittest.TestCase):

    def test_one_handler(self):
        'Reverse one match'
        r = web.Reverse.from_handler(web.match('/', 'index'))
        self.assertEqual(r.index.as_url, '/')

    def test_deafult_name(self):
        'Reverse default name'
        app = web.cases(
            web.match('/'),
            web.match('/index', 'index'),
        )
        r = web.Reverse.from_handler(app)
        self.assertEqual(r.as_url, '/')
        self.assertEqual(r.index.as_url, '/index')

    def test_deafult_name_with_args(self):
        'Reverse default name with args'
        app = web.match('/<arg>')

        r = web.Reverse.from_handler(app)
        self.assertEqual(r(arg='1').as_url, '/1')
        self.assertRaises(UrlBuildingError, lambda: r.as_url)

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

    def test_nested_prefix_without_ns(self):
        chain = web.prefix('/docs', name='docs') | web.cases(
            web.match('/', name='all'),
            web.prefix('/news') | web.cases(
                web.match('/', 'news_index'),
                web.match('/all', 'news_all')
            )
        )
        r = web.Reverse.from_handler(chain)
        self.assertEqual(r.docs.all.as_url, '/docs/')
        self.assertEqual(r.docs.news_index.as_url, '/docs/news/')

    def test_subreverse(self):
        chain = web.cases(
                web.prefix('/docs', name='docs') | web.cases(
                    web.match('/<int:id>', 'doc'),
                    web.match('/list', 'docs')))

        r = web.Reverse.from_handler(chain)
        self.assertEqual(r.build_subreverse('docs.doc', id=1).as_url, '/docs/1')
        self.assertEqual(r.build_subreverse('docs').doc(id=1).as_url, '/docs/1')

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
        self.assertEqual(str(r.unicode1), 'http://xn--o1a/%D0%B7/')
        self.assertEqual(r.unicode2(slug=u'ю').as_url, 'http://xn--o1a/%D0%B7/%D1%8E')
        self.assertEqual(r.unicode3(slug=u'ю').as_url, 'http://xn--o1a/%D0%B4/%D1%8E')
        self.assertEqual(r.unicode4(slug1=u'д', slug2=u'ю').as_url, 'http://xn--o1a/%D0%B4/%D1%8E')

    def test_port(self):
        chain = web.subdomain(u'example.com:8000') | web.match('/', name="index")
        r = web.Reverse.from_handler(chain)
        self.assertEqual(r.index.as_url.port, '8000')
        self.assertEqual(r.index.as_url.host, 'example.com')

    def test_nested_prefixes(self):
        'Reverse with nested prefexes'
        app = web.prefix('/news/<section>', name='news') | web.cases(
                web.match(),
                web.prefix('/<int:id>', name='item') | web.cases(
                    web.match(),
                    web.prefix('/docs', name='docs') | web.cases(
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
        # XXX this one raises KeyError, not UrlBuildingError
        self.assertRaises(UrlBuildingError, lambda: r.news(foo='top').as_url)
        self.assertRaises(UrlBuildingError, lambda: r.news(section='top').item.as_url)
        self.assertRaises(UrlBuildingError, lambda: r.news(section='top').item(id=1).docs())
        self.assertRaises(UrlBuildingError, lambda: r.news(section='top')())
        self.assertRaises(UrlBuildingError, lambda: r.news.item)

    def test_endpoint_with_params(self):
        app = web.prefix('/news', name='news') | web.cases(
                web.match('/<sort>'),
                web.match('/<sort>/page/<int:page>', name='page'),
                web.match('/feed', name='feed'),
        )
        r = web.Reverse.from_handler(app)

        self.assertEqual(r.news(sort="desc").as_url, '/news/desc')
        self.assertEqual(r.news.page(sort="desc", page=1).as_url, '/news/desc/page/1')
        self.assertEqual(r.news.feed.as_url, '/news/feed')

    @unittest.expectedFailure
    def test_endpoint_with_params2(self):
        app = web.prefix('/news', name='news') | web.cases(
                web.match('/<sort>'),
                web.match('/<sort>/page/<int:page>', name='page'),
                web.match('/feed', name='feed'),
        )
        r = web.Reverse.from_handler(app)

        self.assertEqual(r.news(sort='desc').page(page=1).as_url, '/news/desc/page/1')
        self.assertRaises(UrlBuildingError, lambda: r.news(sort='desc')()())

    def test_string_api(self):
        'String API for reverse (build_url)'
        app = web.prefix('/news/<section>') | web.namespace('news') | web.cases(
                web.match(),
                web.prefix('/<int:id>') | web.namespace('item') | web.cases(
                    web.match(),
                    web.prefix('/docs') | web.namespace('docs') | web.cases(
                        web.match()
                    )))
        r = web.Reverse.from_handler(app)

        # Normal behavior
        self.assertEqual(r.build_url('news', section='top'), '/news/top')
        self.assertEqual(r.build_url('news.item', section='top', id=1), '/news/top/1')
        self.assertEqual(r.build_url('news.item.docs', section='top', id=1), '/news/top/1/docs')

        # Exceptional behavior
        self.assertRaises(UrlBuildingError, r.build_url, 'news')
        self.assertRaises(UrlBuildingError, r.build_url, 'news', 
                          section='top', subsection="bottom")

    def test_prefix_after_namespace(self):
        app = web.prefix('/news', name='news') | web.prefix('/<section>') | web.cases(
                web.match(),
                web.match('/<int:id>', 'item'),
                )
        r = web.Reverse.from_handler(app)
        self.assertEqual(r.build_url('news.item', section='top', id=1), '/news/top/1')
        self.assertEqual(r.build_url('news', section='top'), '/news/top')
        self.assertEqual(r.news(section='top').item(id=1).as_url, '/news/top/1')
        self.assertEqual(r.news(section='top').as_url, '/news/top')

    def test_subdomain_after_namespace(self):
        app = web.subdomain('news', name='news') | web.subdomain('eng') | web.cases(
                web.match('/'),
                web.match('/<int:id>', 'item'),
                )
        r = web.Reverse.from_handler(app)
        self.assertEqual(r.build_url('news.item', id=1), 'http://eng.news/1')
        self.assertEqual(r.build_url('news'), 'http://eng.news/')
        self.assertEqual(r.news.item(id=1).as_url, 'http://eng.news/1')
        self.assertEqual(r.news.as_url, 'http://eng.news/')

    def test_external_urls(self):
        'External URL reverse'

        def host1(env, data):
            self.assertEqual(env.root.host1.as_url.with_host(), 'http://host1.example.com/url')
            self.assertEqual(env.root.host2.as_url, 'http://host2.example.com/url')
            self.assertEqual(env.root.host1.as_url, '/url')
            self.host1_called = True
            return Response()

        def host2(env, data):
            self.assertEqual(env.root.host2.as_url.with_host(), 'https://host2.example.com/url')
            self.assertEqual(env.root.host1.as_url, 'https://host1.example.com/url')
            self.assertEqual(env.root.host2.as_url, '/url')
            self.host2_called = True
            return Response()

        app = web.subdomain('example.com') | web.cases (
            web.subdomain('host1') | web.match('/url', 'host1') | host1,
            web.subdomain('host2') | web.match('/url', 'host2') | host2,
        )

        assert web.ask(app, 'http://host1.example.com/url')
        assert web.ask(app, 'https://host2.example.com/url')
        assert self.host1_called and self.host2_called

    def test_external_urls_no_port(self):
        'External URL reverse with no port in Request.host (sometimes happens using Flup)'

        def host1(env, data):
            if ':' in env.request.host:
                env.request.host = env.request.host.split(':')[0]
            self.assertEqual(env.root.host1.as_url.with_host(), 'http://host1.example.com/url')
            self.assertEqual(env.root.host2.as_url, 'http://host2.example.com/url')
            self.assertEqual(env.root.host1.as_url, '/url')
            self.host1_called = True
            return Response()

        app = web.subdomain('example.com') | web.cases (
            web.subdomain('host1') | web.match('/url', 'host1') | host1,
            web.subdomain('host2') | web.match('/url', 'host2'),
        )

        assert web.ask(app, 'http://host1.example.com/url')
        assert self.host1_called

    def test_external_urls_no_subdomain(self):
        'External URL reverse with no subdomains provided in location'
        def config(env, data, nxt):
            env.root = root.bind_to_env(env)
            return nxt(env, data)

        called_urls = []

        def get_handler(num, result):
            def handler(env, data):
                self.assertEqual(env.root.url1.as_url.with_host(), result)
                called_urls.append(num)
                return Response()
            return handler

        url1 = get_handler(1, 'http://example.com/url')
        url2 = get_handler(2, 'http://example.com:8000/url')
        url3 = get_handler(3, 'https://example.com:80/url')

        app = web.request_filter(config) | web.cases(
                web.match('/url', 'url1') | url1,
                web.match('/url2', 'url2') | url2,
                web.match('/url3', 'url3') | url3,
                )
        root = web.Reverse.from_handler(app)

        assert web.ask(app, 'http://example.com/url')
        assert web.ask(app, 'http://example.com:8000/url2')
        assert web.ask(app, 'https://example.com:80/url3')
        assert called_urls == [1,2,3]
        
    def test_url_building_errors(self):
        'UrlBuildingError'
        app = web.namespace('news') | web.cases(
                web.match('/', 'index'),
                web.match('/<int:id>', 'item'),
                )

        r = web.Reverse.from_handler(app)
        self.assertRaises(UrlBuildingError, r.build_url, '')
        self.assertRaises(UrlBuildingError, lambda: r.as_url)

        self.assertRaises(UrlBuildingError, r.build_url, 'main')
        self.assertRaises(UrlBuildingError, lambda: r.main)

        self.assertRaises(UrlBuildingError, r.build_url, 'news.item')
        self.assertRaises(UrlBuildingError, lambda: r.news.item.as_url)

        self.assertRaises(UrlBuildingError, r.build_url, 'news.item', section='x')
        self.assertRaises(UrlBuildingError, lambda: r.news.item(section='x'))

        self.assertRaises(UrlBuildingError, r.build_url, 'news')
        self.assertRaises(UrlBuildingError, lambda: r.news.as_url)

    def test_multiple_params(self):
        app = web.prefix('/persons/<int:person_id>') | web.namespace('persons') |\
                web.cases(
                  web.prefix('/news') | web.namespace('news') |
                     web.match('/<int:news_id>', 'item')
                )
        r = web.Reverse.from_handler(app)
        r1 = r.persons(person_id=1).news.item(news_id=2)
        self.assertEqual(r1.as_url, '/persons/1/news/2')
        self.assertEqual(r.build_url('persons.news.item', person_id=1,
                                     news_id=2),
                         '/persons/1/news/2')

    def test_multiple_params2(self):
        app = web.prefix('/persons') | web.namespace('persons') |\
                web.prefix('/<int:person_id>') | web.cases(
                  web.prefix('/news') | web.namespace('news') |
                     web.match('/<int:news_id>', 'item')
                )
        r = web.Reverse.from_handler(app)
        r1 = r.persons.news(person_id=1).item(news_id=2)
        self.assertEqual(r1.as_url, '/persons/1/news/2')
        self.assertEqual(r.build_url('persons.news.item', person_id=1,
                                     news_id=2),
                         '/persons/1/news/2')

    def test_multiple_params_with_endpoints(self):
        app = web.prefix('/persons/<int:person_id>') | web.namespace('persons') |\
                web.cases(
                  web.match('/index', ''),
                  web.prefix('/news') | web.namespace('news') | web.cases(
                     web.match('/index', ''),
                     web.match('/<int:news_id>', 'item')
                  )
                )
        r = web.Reverse.from_handler(app)
        r1 = r.persons(person_id=1).news.item(news_id=2)
        self.assertEqual(r1.as_url, '/persons/1/news/2')
        self.assertEqual(r.build_url('persons.news.item', person_id=1,
                                     news_id=2),
                         '/persons/1/news/2')

    def test_multiple_params_with_params_in_endpoints(self):
        app = web.prefix('/persons/<int:person_id>') | web.namespace('persons') |\
                web.cases(
                  web.match('/index/<page>', ''),
                  web.prefix('/news') | web.namespace('news') | web.cases(
                     web.match('/index/<news_page>', ''),
                     web.match('/<int:news_id>', 'item')
                  )
                )
        r = web.Reverse.from_handler(app)
        self.assertEqual(r.persons(person_id=1, page=2).as_url, '/persons/1/index/2')
        self.assertEqual(r.build_url('persons', person_id=1, page=2),
                         '/persons/1/index/2')
        self.assertRaises(UrlBuildingError,
                          lambda: r.persons(person_id=1).as_url)
        self.assertRaises(UrlBuildingError,
                          lambda: r.persons(person_id=1).news.as_url)


    def test_subdomains_and_namespace(self):
        app = web.subdomain('d2') | web.namespace('subdomain') | \
                web.subdomain('d1') | web.namespace('more') | \
                web.match('/', 'index')
        r = web.Reverse.from_handler(app)
        self.assertEqual(r.subdomain.more.index.as_url, 'http://d1.d2/')

    def test_default_values(self):
        app = web.prefix('/<int(default=0):id1>', name='ns') | web.cases(
                web.match('/<int(default=0):id2>'),
                web.match('/n/<int(default=0):id2>', 'nested'),
                web.prefix('/o', name='other') | web.cases(
                    web.match('/<int(default=0):id3>'),
                ),
            )
        r = web.Reverse.from_handler(app)

        self.assertEqual(r.ns.as_url, '/0/0')
        self.assertEqual(r.ns(id1=1, id2=2).as_url, '/1/2')
        self.assertEqual(r.ns(id2=2).as_url, '/0/2')

        self.assertEqual(r.ns.other.as_url, '/0/o/0')
        self.assertEqual(r.ns.other(id3=1).as_url, '/0/o/1')

        self.assertEqual(r.ns.nested.as_url, '/0/n/0')
        self.assertEqual(r.ns().nested().as_url, '/0/n/0')
        self.assertEqual(r.ns(id1=1).nested(id2=2).as_url, '/1/n/2')
        self.assertEqual(r.build_url('ns.nested'), '/0/n/0')
        self.assertEqual(r.build_url('ns.nested', id1=1, id2=2), '/1/n/2')

