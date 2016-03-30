# -*- coding: utf-8 -*-
import unittest
from iktomi.utils.paginator import Paginator
from webob import Request

class PaginatorTest(unittest.TestCase):

    def test_paginator_basics(self):
        request = Request.blank('/?page=5')
        paginator = Paginator(request=request,
                              count=100,
                              limit=10)
        self.assertEqual(paginator.pages_count, 10)
        self.assertEqual(paginator.page, 5)
        self.assertEqual(paginator.page_url(7), '/?page=7')
        paginator.items = paginator.slice(range(100))
        self.assertEqual(paginator.items, range(40, 50))
        self.assertEqual(list(paginator.enumerate()),
                         zip(range(41, 51), range(40, 50)))

    def test_orphans(self):
        request = Request.blank('/?page=10')
        paginator = Paginator(request=request,
                              count=105,
                              limit=10)
        self.assertEqual(paginator.pages_count, 11)
        self.assertEqual(paginator.page, 10)
        self.assertEqual(paginator.slice(range(105)), range(90, 100))
        # using orphans
        paginator = Paginator(request=request,
                              count=105,
                              orphans=7,
                              limit=10)
        self.assertEqual(paginator.pages_count, 10)
        self.assertEqual(paginator.page, 10)
        self.assertEqual(paginator.slice(range(105)), range(90, 105))

        paginator.items = paginator.slice(range(105))
        self.assertEqual(list(paginator.enumerate()),
                         zip(range(91, 106), range(90, 105)))
