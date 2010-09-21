# -*- coding: utf-8 -*-

import unittest

from insanities.forms import *
from webob.multidict import MultiDict
from .testutils import FormTestCase, MockField


class ConverterTests(FormTestCase):

    def test_accept(self):
        'Accept method of converter'
        field = MockField(convs.Converter, self.env())
        conv = field.conv
        value = conv.to_python('value')
        self.assertEqual(value, 'value')

    def test_to_python(self):
        'Converter to_python method'
        field = MockField(convs.Converter, self.env())
        conv = field.conv
        value = conv.to_python('value')
        self.assertEqual(value, 'value')

    def test_from_python(self):
        'Converter from_python method'
        field = MockField(convs.Converter, self.env())
        conv = field.conv
        value = conv.from_python('value')
        self.assertEqual(value, 'value')


class IntConverterTests(FormTestCase):

    def test_accept_valid(self):
        'Accept method of Int converter'
        field = MockField(convs.Int, self.env())
        conv = field.conv
        value = conv.to_python('12')
        self.assertEqual(value, 12)

    def test_accept_invalid(self):
        'Accept method of Int converter for invalid data'
        field = MockField(convs.Int, self.env())
        conv = field.conv
        self.assertRaises(convs.ValidationError, conv.to_python, '12c')

    def test_accept_null_value(self):
        'Accept method of Int converter for None value'
        field = MockField(convs.Int(required=False), self.env())
        conv = field.conv
        value = conv.to_python('')
        self.assertEqual(value, None)

    def test_to_python(self):
        'Int Converter to_python method'
        field = MockField(convs.Int, self.env())
        conv = field.conv
        value = conv.to_python('12')
        self.assertEqual(value, 12)

    def test_from_python(self):
        'Int Converter from_python method'
        field = MockField(convs.Int, self.env())
        conv = field.conv
        value = conv.from_python(12)
        self.assertEqual(value, u'12')


class CharConverterTests(FormTestCase):

    def test_accept_valid(self):
        'Accept method of Char converter'
        field = MockField(convs.Char, self.env())
        conv = field.conv
        value = conv.to_python('12')
        self.assertEqual(value, u'12')

    def test_accept_null_value(self):
        'Accept method of Char converter for None value'
        field = MockField(convs.Char(required=False), self.env())
        conv = field.conv
        value = conv.to_python('')
        self.assertEqual(value, '')

    def test_to_python(self):
        'Char Converter to_python method'
        field = MockField(convs.Char, self.env())
        conv = field.conv
        value = conv.to_python('12')
        self.assertEqual(value, u'12')

    def test_from_python(self):
        'Char Converter from_python method'
        field = MockField(convs.Char, self.env())
        conv = field.conv
        value = conv.from_python(12)
        self.assertEqual(value, u'12')
