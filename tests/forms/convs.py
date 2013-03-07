# -*- coding: utf-8 -*-

import unittest

from iktomi.forms import *
from webob.multidict import MultiDict


def init_conv(conv, name='name'):
    class f(Form):
        fields = [Field(name, conv)]
    return f().get_field(name).conv


class ConverterTests(unittest.TestCase):

    def test_accept(self):
        'Accept method of converter'
        conv = init_conv(convs.Converter)
        value = conv.to_python('value')
        self.assertEqual(value, 'value')

    def test_to_python(self):
        'Converter to_python method'
        conv = init_conv(convs.Converter)
        value = conv.to_python('value')
        self.assertEqual(value, 'value')

    def test_from_python(self):
        'Converter from_python method'
        conv = init_conv(convs.Converter)
        value = conv.from_python('value')
        self.assertEqual(value, 'value')


class IntConverterTests(unittest.TestCase):

    def test_accept_valid(self):
        'Accept method of Int converter'
        conv = init_conv(convs.Int)
        value = conv.to_python('12')
        self.assertEqual(value, 12)

    def test_accept_null_value(self):
        'Accept method of Int converter for None value'
        conv = init_conv(convs.Int(required=False))
        value = conv.to_python('')
        self.assertEqual(value, None)

    def test_to_python(self):
        'Int Converter to_python method'
        conv = init_conv(convs.Int)
        value = conv.to_python('12')
        self.assertEqual(value, 12)

    def test_from_python(self):
        'Int Converter from_python method'
        conv = init_conv(convs.Int)
        value = conv.from_python(12)
        self.assertEqual(value, u'12')

class EnumChoiceConverterTests(unittest.TestCase):

    def test_accept_valid(self):
        'Accept method of Int converter'
        conv = init_conv(convs.EnumChoice(choices=[
            (1, 'result')
        ], conv=convs.Int()))

        value = conv.to_python('1')
        self.assertEqual(value, 1)

    def test_accept_null_value(self):
        'Accept method of EnumChoice converter for None value'
        conv = init_conv(convs.EnumChoice(choices=[
            (1, 'result')
        ], conv=convs.Int(), required=False))

        value = conv.to_python('')
        self.assertEqual(value, None)

    def test_accept_invalid_value(self):
        'Accept method of EnumChoice converter for None value'
        conv = init_conv(convs.EnumChoice(choices=[
            (1, 'result')
        ], conv=convs.Int(), required=False))

        value = conv.to_python('unknown')
        self.assertEqual(value, None)

    def test_accept_missing_value(self):
        'Accept method of EnumChoice converter for None value'
        conv = init_conv(convs.EnumChoice(choices=[
            (1, 'result')
        ], conv=convs.Int(), required=False))

        value = conv.to_python('2')
        self.assertEqual(value, None)

    def test_decline_null_value(self):
        'Accept method of EnumChoice required converter for None value'
        conv = init_conv(convs.EnumChoice(choices=[
            (1, 'result')
        ], conv=convs.Int(), required=True))

        value = conv.to_python('')
        self.assertEqual(value, None)
        self.assertEqual(conv.field.form.errors.keys(),
                         [conv.field.name])

    def test_decline_invalid_value(self):
        'Accept method of EnumChoice required converter for invalid value'
        conv = init_conv(convs.EnumChoice(choices=[
            (1, 'result')
        ], conv=convs.Int(), required=True))
        value = conv.to_python('invalid')
        self.assertEqual(value, None)
        self.assertEqual(conv.field.form.errors.keys(),
                         [conv.field.name])

    def test_decline_missing_value(self):
        'Accept method of EnumChoice required converter for missing value'
        conv = init_conv(convs.EnumChoice(choices=[
            (1, 'result')
        ], conv=convs.Int(), required=True))
        value = conv.to_python('2')
        self.assertEqual(value, None)
        self.assertEqual(conv.field.form.errors.keys(),
                         [conv.field.name])

    def test_from_python(self):
        'EnumChoice Converter from_python method'
        conv = init_conv(convs.EnumChoice(choices=[
            (1, 'result')
        ], conv=convs.Int(), required=False))

        value = conv.from_python(1)
        self.assertEqual(value, u'1')


class CharConverterTests(unittest.TestCase):

    def test_accept_valid(self):
        'Accept method of Char converter'
        conv = init_conv(convs.Char)
        value = conv.to_python('12')
        self.assertEqual(value, u'12')

    def test_accept_null_value(self):
        'Accept method of Char converter for None value'
        conv = init_conv(convs.Char(required=False))
        value = conv.to_python('')
        self.assertEqual(value, '')

    def test_to_python(self):
        'Char Converter to_python method'
        conv = init_conv(convs.Char)
        value = conv.to_python('12')
        self.assertEqual(value, u'12')

    def test_from_python(self):
        'Char Converter from_python method'
        conv = init_conv(convs.Char)
        value = conv.from_python(12)
        self.assertEqual(value, u'12')

class TestDate(unittest.TestCase):

    def test_accept_valid(self):
        '''Date converter to_python method'''
        from datetime import date
        conv = init_conv(convs.Date(format="%d.%m.%Y"))
        self.assertEqual(conv.to_python('31.01.1999'), date(1999, 1, 31))

    def test_readable_format(self):
        '''Ensure that readable format string for DateTime conv is generated correctly'''
        conv = convs.Date(format="%d.%m.%Y")()
        self.assertEqual(conv.readable_format, 'DD.MM.YYYY')

    def test_from_python(self):
        '''Date converter from_python method'''
        from datetime import date
        conv = init_conv(convs.Date(format="%d.%m.%Y"))
        self.assertEqual(conv.from_python(date(1999, 1, 31)), '31.01.1999')

    def test_from_python_pre_1900(self):
        # XXX move this tests to tests.utils.dt
        '''Test if from_python works fine with dates under 1900'''
        from datetime import date
        conv = init_conv(convs.Date(format="%d.%m.%Y"))
        self.assertEqual(conv.from_python(date(1899, 1, 31)), '31.01.1899')
        self.assertEqual(conv.from_python(date(401, 1, 31)), '31.01.401')

        conv = init_conv(convs.Date(format="%d.%m.%y"))
        # XXX is it right?
        self.assertEqual(conv.from_python(date(1899, 1, 31)), '31.01.99')
        self.assertEqual(conv.from_python(date(5, 1, 31)), '31.01.05')

class TestTime(unittest.TestCase):

    def test_from_python(self):
        '''Time converter from_python method'''
        from datetime import time
        conv = init_conv(convs.Time)
        self.assertEqual(conv.from_python(time(12, 30)), '12:30')

    def test_to_python(self):
        '''Time converter to_python method'''
        from datetime import time
        conv = init_conv(convs.Time)
        self.assertEqual(conv.to_python('12:30'), time(12, 30))

