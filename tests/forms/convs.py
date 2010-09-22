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

#lass TestDate(TestFormClass):

#   def test_from_python(self):
#       from datetime import date
#       conv = convs.Date(format="%d.%m.%Y")
#       conv = self.instantiate_conv(conv)
#       self.assertEqual(conv.from_python(date(1999, 1, 31)), '31.01.1999')

#   def test_from_python_pre_1900(self):
#       '''Test if from_python works fine with dates under 1900'''
#       from datetime import date
#       conv = convs.Date(format="%d.%m.%Y")
#       conv = self.instantiate_conv(conv)
#       self.assertEqual(conv.from_python(date(1899, 1, 31)), '31.01.1899')
#       self.assertEqual(conv.from_python(date(401, 1, 31)), '31.01.401')

#       conv = convs.Date(format="%d.%m.%y")
#       conv = self.instantiate_conv(conv)
#       # XXX is it right?
#       self.assertEqual(conv.from_python(date(1899, 1, 31)), '31.01.99')
#       self.assertEqual(conv.from_python(date(5, 1, 31)), '31.01.05')

#   def test_to_python(self):
#       from datetime import date

#       conv = convs.Date(format="%d.%m.%Y")
#       conv = self.instantiate_conv(conv)
#       self.assertEqual(conv.accept('31.01.1999'), date(1999, 1, 31))

#       conv = convs.Date(format="%d.%m.%Y")
#       conv = self.instantiate_conv(conv)
#       try:
#           conv.accept('abc')
#       except convs.ValidationError, e:
#           self.assertEqual(e.message, 'Wrong format (DD.MM.YYYY)')
#       else:
#           self._assert(False, 'ValidationError not raised')

#   def test_type_error(self):
#       '''In some cases Date\DateTime\Time converters should use'''
#       conv = convs.Date()
#       conv = self.instantiate_conv(conv)
#       self.assertRaises(convs.ValidationError, conv.accept, '\x00abc')

#lass TestDate(TestFormClass):

#   def test_from_python(self):
#       from datetime import time
#       conv = convs.Time()
#       conv = self.instantiate_conv(conv)
#       self.assertEqual(conv.from_python(time(12, 30)), '12:30')

#   def test_to_python(self):
#       from datetime import time

#       conv = convs.Time()
#       conv = self.instantiate_conv(conv)
#       self.assertEqual(conv.accept('12:30'), time(12, 30))

