# -*- coding: utf-8 -*-

import unittest
from insanities.web.url_templates import *


class IntConverter(unittest.TestCase):

    def test_to_python(self):
        conv = Integer()
        value = conv.to_python(u'4')
        self.assertEqual(value, 4)

    def test_to_python_fail(self):
        conv = Integer()
        self.assertRaises(ConvertError, lambda : conv.to_python(u'4w'))

    def test_to_url(self):
        conv = Integer()
        value = conv.to_url(4)
        self.assertEqual(value, '4')


class StringConverter(unittest.TestCase):

    def test_url_template(self):
        ut = UrlTemplate('/<string(min=3, max=6):message>')

        self.assertEqual(ut.match('/si'), (False, {}))
        self.assertEqual(ut.match('/siga'), (True, {'message': 'siga'}))
        self.assertEqual(ut.match('/sigadzuk'), (False, {}))


    def test_to_python(self):
        self.assertEqual(String().to_python(u'a'), u'a')

    def test_to_url(self):
        self.assertEqual(String().to_url(u'a'), u'a')
