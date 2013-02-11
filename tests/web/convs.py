# -*- coding: utf-8 -*-

import re
import unittest
from iktomi.web.url_templates import *
from iktomi.web.url_converters import *
from datetime import date


class IntConverter(unittest.TestCase):

    def test_to_python(self):
        conv = Integer()
        value = conv.to_python(u'4')
        self.assertEqual(value, 4)

    def test_to_python_fail(self):
        conv = Integer()
        self.assertRaises(ConvertError, lambda : conv.to_python(u'4w'))
        assert not re.match(conv.regex, '004')
        assert not re.match(conv.regex, '  4')
        #self.assertRaises(ConvertError, lambda : conv.to_python(u'004'))
        #self.assertRaises(ConvertError, lambda : conv.to_python(u'  4'))

    def test_to_url(self):
        conv = Integer()
        value = conv.to_url(4)
        self.assertEqual(value, '4')


class StringConverter(unittest.TestCase):

    def test_min_max(self):
        ut = UrlTemplate('/<string(min=3, max=6):message>')

        self.assertEqual(ut.match('/si'), (None, {}))
        self.assertEqual(ut.match('/siga'), ('/siga', {'message': 'siga'}))
        self.assertEqual(ut.match('/sigadzuk'), (None, {}))


    def test_to_python(self):
        self.assertEqual(String().to_python(u'a'), u'a')

    def test_to_url(self):
        self.assertEqual(String().to_url(u'a'), u'a')


class DateConverter(unittest.TestCase):

    def test_to_python(self):
        self.assertEqual(Date().to_python('2012-10-24'),
                         date(year=2012, month=10, day=24))

        self.assertEqual(Date(format="%Y%m%d").to_python('20121024'),
                         date(year=2012, month=10, day=24))

        self.assertRaises(ConvertError,
                          Date().to_python, '20121024')

    def test_to_url(self):
        self.assertEqual(Date().to_url(
                             date(year=2012, month=10, day=24)),
                         u'2012-10-24')
