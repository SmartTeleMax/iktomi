# -*- coding: utf-8 -*-

__all__ = ['PaginatorTests']

import unittest
from iktomi.utils.paginator import Paginator, ModelPaginator, \
        FancyPageRange, ChunkedPageRange
from iktomi.web.url import URL
from webob import Request
from webob.exc import HTTPNotFound


class MockQuery(list):

    def count(self):
        return len(self)


NONE = (None, None)

class PaginatorTests(unittest.TestCase):

    def test_page_object(self):
        paginator = Paginator(limit=4,
                              count=0,
                              request=Request.blank('/news'))
        self.assertFalse(bool(paginator.next))
        self.assertEqual(paginator.last.page, 1)
        self.assertEqual(paginator.last.url, '/news')
        self.assertIsInstance(paginator.last.url, URL)

    def test_empty(self):
        paginator = Paginator(limit=4,
                              count=0,
                              request=Request.blank('/news'))

        self.assertEqual(paginator.count, 0)
        self.assertEqual(paginator.page, 1)
        self.assertEqual(paginator.pages_count, 1)
        self.assertEqual(paginator.prev, NONE)
        self.assertEqual(paginator.next, NONE)
        self.assertEqual(paginator.first, (1, '/news'))
        self.assertEqual(paginator.last, (1, '/news'))
        self.assertEqual(paginator.pages, [(1, '/news')])

    def test_no_limit(self):
        def pages(paginator):
            return [x.page for x in paginator.pages]
        paginator = Paginator(count=10,
                              request=Request.blank('/news'))
        paginator.items = paginator.slice(range(8))

        self.assertEqual(paginator.count, 10)
        self.assertEqual(paginator.page, 1)
        self.assertEqual(paginator.pages_count, 1)
        self.assertEqual(paginator.prev, NONE)
        self.assertEqual(paginator.next, NONE)
        self.assertEqual(paginator.first, (1, '/news'))
        self.assertEqual(paginator.last, (1, '/news'))
        self.assertEqual(pages(paginator), [1])
        self.assertEqual(paginator.items, [0,1,2,3,4,5,6,7])

    def test_not_existing_page(self):
        paginator = Paginator(limit=4,
                              count=8,
                              request=Request.blank('/news?page=3'))
        paginator.items = paginator.slice(range(8))

        self.assertEqual(paginator.count, 8)
        self.assertEqual(paginator.page, 3)
        self.assertEqual(paginator.pages_count, 2)
        self.assertEqual(paginator.prev, (2, '/news?page=2'))
        self.assertEqual(paginator.next, NONE)
        self.assertEqual(paginator.first, (1, '/news'))
        self.assertEqual(paginator.last, (2, '/news?page=2'))
        self.assertEqual(paginator.pages, [(1, '/news'),
                                           (2, '/news?page=2')])
        self.assertEqual(paginator.items, [])

        paginator = Paginator(limit=4,
                              count=8,
                              request=Request.blank('/news?page=10'))
        self.assertEqual(paginator.prev, (2, '/news?page=2'))

    def test_last_page(self):
        paginator = Paginator(limit=4,
                              count=5,
                              request=Request.blank('/news?page=2'))
        paginator.items = paginator.slice(range(5))

        self.assertEqual(paginator.count, 5)
        self.assertEqual(paginator.page, 2)
        self.assertEqual(paginator.pages_count, 2)
        self.assertEqual(paginator.prev, (1, '/news'))
        self.assertEqual(paginator.next, NONE)
        self.assertEqual(paginator.first, (1, '/news'))
        self.assertEqual(paginator.last, (2, '/news?page=2'))
        self.assertEqual(paginator.pages, [(1, '/news'),
                                           (2, '/news?page=2')])
        self.assertEqual(paginator.items, [4])

    def test_page_param(self):
        paginator = Paginator(limit=4,
                              count=9,
                              request=Request.blank('/news?p=2'),
                              page_param='p')
        paginator.items = paginator.slice(range(5))

        self.assertEqual(paginator.next.url, '/news?p=3')

    def test_enumerate(self):
        paginator = Paginator(limit=4,
                              count=6,
                              request=Request.blank('/news?p=2'),
                              page_param='p')
        paginator.items = paginator.slice(range(6))

        self.assertEqual(list(paginator.enumerate()), [
            (5, 4), (6, 5),
        ])

    def test_model_paginator(self):
        query = MockQuery(range(20))
        paginator = ModelPaginator(Request.blank('/news?page=2'),
                                   query,
                                   limit=4)

        self.assertEqual(paginator.count, 20)
        self.assertEqual(paginator.page, 2)
        self.assertEqual(paginator.pages_count, 5)
        self.assertEqual(paginator.items, [4, 5, 6, 7])
        self.assertEqual(list(paginator), [4, 5, 6, 7])
        self.assertEqual(len(paginator), 4)
        self.assertEqual(paginator[0], 4)

    def test_fancy(self):
        def pages(paginator):
            return [x.page for x in paginator.pages]

        # in the middle
        impl = FancyPageRange(edge=2, surround=3)
        paginator = Paginator(Request.blank('/news?page=50'),
                              limit=1, count=100, impl=impl)
        self.assertEqual(pages(paginator), [
            1, 2, None, 47, 48, 49, 50, 51, 52, 53, None, 99, 100])

        # at the start
        paginator = Paginator(Request.blank('/news?page=1'),
                              limit=1, count=100, impl=impl)
        self.assertEqual(pages(paginator), [
            1, 2, 3, 4, None, 99, 100])

        # near the start
        paginator = Paginator(Request.blank('/news?page=5'),
                              limit=1, count=100, impl=impl)
        self.assertEqual(pages(paginator), [
            1, 2, 3, 4, 5, 6, 7, 8, None, 99, 100])

        # outside the range
        paginator = Paginator(Request.blank('/news?page=200'),
                              limit=1, count=100, impl=impl)
        self.assertEqual(pages(paginator), [
            1, 2, None, 99, 100])

        # near the end
        impl = FancyPageRange(edge=2, surround=5)
        paginator = Paginator(Request.blank('/news?page=99'),
                              limit=1, count=100, impl=impl)
        self.assertEqual(pages(paginator), [
            1, 2, None, 94, 95, 96, 97, 98, 99, 100])

        # one range inside another
        impl = FancyPageRange(edge=8, surround=2)
        paginator = Paginator(Request.blank('/news?page=4'),
                              limit=1, count=100, impl=impl)
        self.assertEqual(pages(paginator), [
            1, 2, 3, 4, 5, 6, 7, 8, None, 93, 94, 95, 96, 97, 98, 99, 100])

        # short paginator
        impl = FancyPageRange(edge=2, surround=5)
        paginator = Paginator(Request.blank('/news?page=99'),
                              limit=1, count=2, impl=impl)
        self.assertEqual(pages(paginator), [1, 2])

    def test_chunked(self):
        def pages(paginator):
            return [x.page for x in paginator.pages]

        impl = ChunkedPageRange(size=3)
        paginator = Paginator(Request.blank('/news?page=1'),
                              limit=1, count=100, impl=impl)
        self.assertEqual(pages(paginator), [1,2,3])
        self.assertEqual(paginator.chunk_size, 3)
        self.assertEqual(paginator.prev_chunk[0], None)
        self.assertEqual(paginator.next_chunk[0], 4)

        paginator = Paginator(Request.blank('/news?page=100'),
                              limit=1, count=100, impl=impl)
        self.assertEqual(pages(paginator), [100])
        self.assertEqual(paginator.chunk_size, 3)
        self.assertEqual(paginator.prev_chunk[0], 99)
        self.assertEqual(paginator.next_chunk[0], None)

        paginator = Paginator(Request.blank('/news?page=11'),
                              limit=1, count=100, impl=impl)
        self.assertEqual(pages(paginator), [10, 11, 12])
        self.assertEqual(paginator.chunk_size, 3)
        self.assertEqual(paginator.prev_chunk[0], 9)
        self.assertEqual(paginator.next_chunk[0], 13)

        #self.assertRaises(AttributeError, lambda: paginator.something)

    def test_invalid_404(self):
        def invalid_page():
            raise HTTPNotFound()

        def make_paginator(pg):
            paginator = Paginator(Request.blank('/news?page='+pg),
                                  limit=1, count=10,
                                  invalid_page=invalid_page)
            paginator.page
        self.assertRaises(HTTPNotFound, make_paginator, '-1')
        make_paginator('100')

    def test_invalid(self):
        paginator = Paginator(Request.blank('/news?page=xx'), limit=1, count=10)
        self.assertEqual(paginator.page, 1)

        paginator = Paginator(Request.blank('/news?page=-1'), limit=1, count=10)
        self.assertEqual(paginator.page, 1)

    def test_nonzero(self):
        paginator = Paginator(limit=4, count=1,
                              request=Request.blank('/news'))
        self.assertFalse(bool(paginator))

        paginator = Paginator(limit=4, count=1,
                              request=Request.blank('/news?page=2'))
        self.assertTrue(bool(paginator))

        paginator = Paginator(limit=4, count=10,
                              request=Request.blank('/news'))
        self.assertTrue(bool(paginator))

        paginator = Paginator(count=1, request=Request.blank('/news'))
        self.assertFalse(bool(paginator))

    def test_orphans(self):
        request = Request.blank('/?page=10')
        # without boundaries, should be 11 pages
        paginator = Paginator(request=request,
                              count=105,
                              limit=10)
        self.assertEqual(paginator.pages_count, 11)
        self.assertEqual(paginator.page, 10)
        self.assertEqual(paginator.slice(range(105)), range(90, 100))
        # using orphans, count=105, orphans = 5, should be 10 pages
        paginator = Paginator(request=request,
                              count=105,
                              orphans=5,
                              limit=10)
        self.assertEqual(paginator.pages_count, 10)
        self.assertEqual(paginator.page, 10)
        self.assertEqual(paginator.slice(range(105)), range(90, 105))

        paginator.items = paginator.slice(range(105))
        self.assertEqual(list(paginator.enumerate()),
                         zip(range(91, 106), range(90, 105)))
        # using orphans, count=106, orphans = 5, should be 11 pages
        paginator = Paginator(request=request,
                              count=106,
                              orphans=5,
                              limit=10)
        self.assertEqual(paginator.pages_count, 11)
        self.assertEqual(paginator.page, 10)
        self.assertEqual(paginator.slice(range(106)), range(90, 100))

        paginator.items = paginator.slice(range(106))
        self.assertEqual(list(paginator.enumerate()),
                         zip(range(91, 101), range(90, 100)))
