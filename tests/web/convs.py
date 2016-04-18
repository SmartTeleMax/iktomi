# -*- coding: utf-8 -*-

import re
import unittest
from iktomi.web.url_templates import *
from iktomi.web.url_converters import *
from datetime import date


class IntConverter(unittest.TestCase):

    def assertToPython(self, conv, value, result):
        regex = conv.regex+'$'
        if result is None:
            assert not re.match(regex, value)
        else:
            assert re.match(regex, value)
            val = conv.to_python(value)
            self.assertEqual(val, result)

    def test_to_python(self):
        conv = Integer()
        self.assertToPython(conv, u'4', 4)

    def test_to_python_zero(self):
        conv = Integer()
        self.assertToPython(conv, u'0', 0)

    def test_to_python_fail(self):
        conv = Integer()
        self.assertRaises(ConvertError, lambda : conv.to_python(u'4w'))
        self.assertToPython(conv, u'004', None)
        self.assertToPython(conv, u'  4', None)

    def test_to_url(self):
        conv = Integer()
        self.assertEqual(conv.to_url(4), '4')

    def test_placeholder(self):
        conv = Integer()
        self.assertEqual(conv.to_url('REPLACEME'), 'REPLACEME')


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

    def test_regex(self):
        ut = UrlTemplate('/<string(regex="[a-z]+"):message>')
        self.assertEqual(ut.match('/siga'), ('/siga', {'message': 'siga'}))
        self.assertEqual(ut.match('/SIGA'), (None, {}))


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

    def test_placeholder(self):
        conv = Date()
        self.assertEqual(conv.to_url('REPLACEME'), 'REPLACEME')


class AnyConverter(unittest.TestCase):

    def test_to_python(self):
        self.assertEqual(Any('opt1', 'opt2').to_python('opt2'),
                         'opt2')

        self.assertRaises(ConvertError,
                          Any('opt1', 'opt2').to_python,
                          'nooption')

    def test_to_url(self):
        self.assertEqual(Any('opt1', 'opt2').to_url('opt1'),
                         u'opt1')

    #@unittest.skip
    #def test_to_url_wrong(self):
    #    # XXX is this right?
    #    self.assertRaises(ConverterError,
    #                      Any('option1', 'option2').to_url,
    #                      'nooption')
