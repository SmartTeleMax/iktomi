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
        value = conv.accept('value')
        self.assertEqual(value, 'value')
        self.assertEqual(conv.field.form.errors, {})

    def test_to_python(self):
        'Converter to_python method'
        conv = init_conv(convs.Converter)
        value = conv.accept('value')
        self.assertEqual(value, 'value')
        self.assertEqual(conv.field.form.errors, {})

    def test_from_python(self):
        'Converter from_python method'
        conv = init_conv(convs.Converter)
        value = conv.from_python('value')
        self.assertEqual(value, 'value')
        self.assertEqual(conv.field.form.errors, {})

    def test_obsolete(self):
        'Convertor accepting obsolete parameters'
        self.assertRaises(DeprecationWarning, convs.Converter, null=True)

    def test_filter(self):
        'Convertor with filters'
        conv = convs.Converter(lambda conv, x: x+'-1', lambda conv, x: x+'-2')
        value = conv.accept('value', silent=True)
        self.assertEqual(value, 'value-1-2')


class IntConverterTests(unittest.TestCase):

    def test_accept_valid(self):
        'Accept method of Int converter'
        conv = init_conv(convs.Int)
        value = conv.accept('12')
        self.assertEqual(value, 12)
        self.assertEqual(conv.field.form.errors, {})

    def test_accept_null_value(self):
        'Accept method of Int converter for None value'
        conv = init_conv(convs.Int(required=False))
        value = conv.accept('')
        self.assertEqual(value, None)
        self.assertEqual(conv.field.form.errors, {})

    def test_from_python(self):
        'Int Converter from_python method'
        conv = init_conv(convs.Int)
        value = conv.from_python(12)
        self.assertEqual(value, u'12')
        self.assertEqual(conv.field.form.errors, {})


class EnumChoiceConverterTests(unittest.TestCase):

    def test_accept_valid(self):
        'Accept method of Int converter'
        conv = init_conv(convs.EnumChoice(choices=[
            (1, 'result')
        ], conv=convs.Int()))

        value = conv.accept('1')
        self.assertEqual(value, 1)
        self.assertEqual(conv.field.form.errors, {})

    def test_accept_null_value(self):
        'Accept method of EnumChoice converter for None value'
        conv = init_conv(convs.EnumChoice(choices=[
            (1, 'result')
        ], conv=convs.Int(), required=False))

        value = conv.accept('')
        self.assertEqual(value, None)
        self.assertEqual(conv.field.form.errors, {})

    def test_accept_invalid_value(self):
        'Accept method of EnumChoice converter for None value'
        conv = init_conv(convs.EnumChoice(choices=[
            (1, 'result')
        ], conv=convs.Int(), required=False))

        value = conv.accept('unknown')
        self.assertEqual(value, None)
        self.assertEqual(conv.field.form.errors.keys(), [])

    def test_accept_missing_value(self):
        'Accept method of EnumChoice converter for None value'
        conv = init_conv(convs.EnumChoice(choices=[
            (1, 'result')
        ], conv=convs.Int(), required=False))

        value = conv.accept('2')
        self.assertEqual(value, None)
        self.assertEqual(conv.field.form.errors, {})

    def test_decline_null_value(self):
        'Accept method of EnumChoice required converter for None value'
        conv = init_conv(convs.EnumChoice(choices=[
            (1, 'result')
        ], conv=convs.Int(), required=True))

        value = conv.accept('')
        self.assertEqual(value, None)
        self.assertEqual(conv.field.form.errors.keys(),
                         [conv.field.name])

    def test_decline_invalid_value(self):
        'Accept method of EnumChoice required converter for invalid value'
        conv = init_conv(convs.EnumChoice(choices=[
            (1, 'result')
        ], conv=convs.Int(), required=True))
        value = conv.accept('invalid')
        self.assertEqual(value, None)
        self.assertEqual(conv.field.form.errors.keys(),
                         [conv.field.name])

    def test_decline_missing_value(self):
        'Accept method of EnumChoice required converter for missing value'
        conv = init_conv(convs.EnumChoice(choices=[
            (1, 'result')
        ], conv=convs.Int(), required=True))
        value = conv.accept('2')
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
        self.assertEqual(conv.field.form.errors, {})


class CharConverterTests(unittest.TestCase):

    def test_accept_valid(self):
        'Accept method of Char converter'
        conv = init_conv(convs.Char)
        value = conv.accept('12')
        self.assertEqual(value, u'12')
        self.assertEqual(conv.field.form.errors, {})

    def test_accept_null_value(self):
        'Accept method of Char converter for None value'
        conv = init_conv(convs.Char(required=False))
        value = conv.accept('')
        self.assertEqual(value, '')
        self.assertEqual(conv.field.form.errors, {})

    def test_accept_null_value_regex(self):
        'Accept empty value by Char converter with non-empty regexp'
        conv = init_conv(convs.Char(regex='.+', required=False))
        value = conv.accept('')
        self.assertEqual(value, '') # XXX
        self.assertEqual(conv.field.form.errors, {})

    def test_regex_error(self):
        conv = init_conv(convs.Char(regex='ZZZ', required=True))
        # XXX This should look like the following:
        #with self.assertRaises(convs.ValidationError) as cm:
        #    conv.accept('AAA')
        #self.assertIn(conv.regex, cm.exception.message)
        conv.accept('AAA')
        field_name = conv.field.name
        errors = conv.field.form.errors
        self.assertEqual(conv.field.form.errors.keys(), [field_name])
        self.assert_(conv.regex in errors[field_name])

    def test_from_python(self):
        'Char Converter from_python method'
        conv = init_conv(convs.Char)
        value = conv.from_python(12)
        self.assertEqual(value, u'12')
        self.assertEqual(conv.field.form.errors, {})

    def test_strip(self):
        'convs.Char.strip tests'
        conv = init_conv(convs.Char(regex="\d+"))
        value = conv.accept(' 12')
        self.assertEqual(value, u'12')
        self.assertEqual(conv.field.form.errors, {})

        conv = init_conv(convs.Char(strip=False))
        value = conv.accept(' 12')
        self.assertEqual(value, u' 12')
        self.assertEqual(conv.field.form.errors, {})

    def test_strip_required(self):
        'convs.Char.strip tests for required'
        conv = init_conv(convs.Char(required=True, strip=True))
        value = conv.accept(' ')
        self.assertEqual(value, None) # XXX
        field_name = conv.field.name
        self.assertEqual(conv.field.form.errors.keys(), [field_name])

    def test_replace_nontext(self):
        'convs.Char.strip tests for required'
        conv = convs.Char(nontext_replacement="?")
        # XXX not all nontext characters are tested
        value = conv.to_python(u'\x00-\x09-\x19-\ud800-\ufffe')
        self.assertEqual(value, '?-\x09-?-?-?')


class BoolConverterTests(unittest.TestCase):

    def test_accept_true(self):
        conv = init_conv(convs.Bool)
        value = conv.accept('xx')
        self.assertEqual(value, True)
        self.assertEqual(conv.field.form.errors, {})

    def test_accept_false(self):
        conv = init_conv(convs.Bool)
        value = conv.accept('')
        self.assertEqual(value, False)
        self.assertEqual(conv.field.form.errors, {})

    def test_required(self):
        conv = init_conv(convs.Bool(required=True))
        value = conv.accept('')
        self.assertEqual(value, False) # XXX is this right?
        field_name = conv.field.name
        self.assertEqual(conv.field.form.errors, {})


class DisplayOnlyTests(unittest.TestCase):

    def test_accept_true(self):
        class f(Form):
            fields = [Field('readonly',
                            conv=convs.DisplayOnly())]
        form = f(initial={'readonly': 'init'})
        form.accept(MultiDict({'readonly': 'value'}))

        self.assertEqual(form.errors, {})
        self.assertEqual(form.python_data, {'readonly': 'init'})


class TestDate(unittest.TestCase):

    def test_accept_valid(self):
        '''Date converter to_python method'''
        from datetime import date
        conv = init_conv(convs.Date(format="%d.%m.%Y"))
        self.assertEqual(conv.accept('31.01.1999'), date(1999, 1, 31))
        self.assertEqual(conv.field.form.errors, {})

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

    def test_accept_nontext(self):
        '''Date converter to_python method accepting non-text characters'''
        from datetime import date
        conv = init_conv(convs.Date(format="%d.%m.%Y"))
        self.assertEqual(conv.accept(u'\uFFFE31.01.1999\x00'), date(1999, 1, 31))
        self.assertEqual(conv.field.form.errors, {})


class TestTime(unittest.TestCase):

    def test_from_python(self):
        '''Time converter from_python method'''
        from datetime import time
        conv = init_conv(convs.Time)
        self.assertEqual(conv.from_python(time(12, 30)), '12:30')
        self.assertEqual(conv.field.form.errors, {})

    def test_to_python(self):
        '''Time converter to_python method'''
        from datetime import time
        conv = init_conv(convs.Time)
        self.assertEqual(conv.accept('12:30'), time(12, 30))
        self.assertEqual(conv.field.form.errors, {})

    def test_accept_nontext(self):
        '''Time converter to_python method'''
        from datetime import time
        conv = init_conv(convs.Time)
        self.assertEqual(conv.accept(u'\x0012:\uFFFE30'), time(12, 30))
        self.assertEqual(conv.field.form.errors, {})


class SplitDateTime(unittest.TestCase):

    def get_form(self, **kwargs):
        class f(Form):
            fields = [FieldSet('dt',
                               conv=convs.SplitDateTime(**kwargs),
                               fields=[
                                Field('date',
                                      conv=convs.Date()),
                                Field('time',
                                      conv=convs.Time()),
                               ])]
        return f


    def test_to_python(self):
        from datetime import datetime
        form = self.get_form()()
        form.accept(MultiDict({'dt.date': '24.03.2013',
                               'dt.time': '13:32'}))
        self.assertEqual(form.python_data, {
            'dt': datetime(2013, 3, 24, 13, 32)
        })
        self.assertEqual(form.errors, {})

    def test_null(self):
        Form = self.get_form()

        form = Form()
        form.accept(MultiDict({'dt.date': '',
                               'dt.time': '13:32'}))
        self.assertEqual(form.python_data, {'dt': None})
        self.assertEqual(form.errors, {})

        form = Form()
        form.accept(MultiDict({'dt.date': '24.03.2013',
                               'dt.time': ''}))
        self.assertEqual(form.python_data, {'dt': None})
        self.assertEqual(form.errors, {})

    def test_required(self):
        Form = self.get_form(required=True)

        form = Form()
        form.accept(MultiDict({'dt.date': '',
                               'dt.time': '13:32'}))
        self.assertEqual(form.errors.keys(), ['dt'])

        form = Form()
        form.accept(MultiDict({'dt.date': '24.03.2013',
                               'dt.time': ''}))
        self.assertEqual(form.errors.keys(), ['dt'])


class PasswordConv(unittest.TestCase):

    def get_form(self, **kwargs):
        from iktomi.forms.shortcuts import PasswordConv
        class f(Form):
            fields = [FieldSet('pass',
                               conv=PasswordConv(**kwargs),
                               fields=[
                                Field('pass'),
                                Field('conf'),
                               ])]
        return f


    def test_to_python(self):
        form = self.get_form()()
        form.accept(MultiDict({'pass.pass': '123123',
                               'pass.conf': '123123'}))
        self.assertEqual(form.python_data, {
            'pass': '123123'
        })
        self.assertEqual(form.errors, {})

    def test_mismatch(self):
        Form = self.get_form()
        form = Form()

        form.accept(MultiDict({'pass.pass': '123123',
                               'pass.conf': '123'}))
        self.assertEqual(form.python_data, {'pass': None})
        self.assertEqual(form.errors.keys(), ['pass'])

    def test_required(self):
        Form = self.get_form(required=True)

        form = Form()
        form.accept(MultiDict({'pass.pass': '',
                               'pass.conf': ''}))
        self.assertEqual(form.errors.keys(), ['pass'])


# XXX tests for SplitDateTime
