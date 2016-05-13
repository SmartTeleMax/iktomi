# -*- coding: utf-8 -*-

import unittest
from datetime import datetime, date, time

from iktomi.forms import *
from iktomi.web.app import AppEnvironment
from webob.multidict import MultiDict
from collections import OrderedDict


def init_conv(conv, name='name'):
    class f(Form):
        fields = [Field(name, conv)]
    env = AppEnvironment.create()
    return f(env).get_field(name).conv


class ConverterTests(unittest.TestCase):

    def test_accept(self):
        'Accept method of converter'
        conv = init_conv(convs.Converter)
        value = conv.accept('value')
        self.assertEqual(value, 'value')
        self.assertEqual(conv.field.form.errors, {})

    def test_accept_emtpy_string(self):
        conv = init_conv(convs.Converter)
        value = conv.accept('')
        self.assertEqual(value, None)
        self.assertEqual(conv.field.form.errors, {})

    def test_repr(self):
        conv = init_conv(convs.Converter(kwarg1="kwargvalue"))
        represented = repr(conv)
        self.assertIn("Converter", represented)
        self.assertIn("field=Field(name='name')", represented)
        self.assertIn("kwarg1='kwargvalue'", represented)

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

    def test_empty_error(self):
        'Converter to_python method'
        def validator(conv, value):
            raise convs.ValidationError()
        conv = init_conv(convs.Converter(validator))
        conv.accept('value')
        self.assertEqual(conv.field.form.errors,
                         {'name': convs.ValidationError.default_message})

    def test_obsolete(self):
        'Convertor accepting obsolete parameters'
        self.assertRaises(TypeError, convs.Converter, null=True)

    def test_filter(self):
        'Convertor with filters'
        conv = convs.Converter(lambda conv, x: x+'-1', lambda conv, x: x+'-2')
        value = conv.accept('value', silent=True)
        self.assertEqual(value, 'value-1-2')

    def test_multiple(self):
        conv = convs.ListOf(convs.Int())
        result = conv.accept(['1', '2', '3'], silent=True)
        self.assertEqual(result, [1, 2, 3])

        result = conv.accept([], silent=True)
        self.assertEqual(result, [])

        result = conv.accept(None, silent=True)
        self.assertEqual(result, [])

        # XXX is this right?
        result = conv.accept(['', '1'], silent=True)
        self.assertEqual(result, [1])

    def test_multiple_validators(self):
        conv = convs.ListOf(convs.Int(lambda conv, x: x+1))
        result = conv.accept(['1', '2', '3'], silent=True)
        self.assertEqual(result, [2, 3, 4])

    def test_validators_copy(self):
        def v1(c, v): pass
        def v2(c, v): pass
        def v3(c, v): pass

        conv = convs.Converter(v1)(v2)

        self.assertEqual(conv.validators, (v1, v2))

        conv = convs.ListOf(convs.Int(v2), v1)
        conv = conv(v3)
        self.assertEqual(conv.validators, (v1, v3))
        self.assertEqual(conv.conv.validators, (v2,))

        conv = convs.Converter(v1)(validators=[])
        self.assertEqual(conv.validators, ())

        conv = convs.Converter(v1)(validators=[v2])
        self.assertEqual(conv.validators, (v2,))

        conv = convs.Converter(v1)(v3, validators=[v2])
        self.assertEqual(conv.validators, (v2, v3))

        conv = convs.Converter(v1)(v3, validators=[v2])(v1)
        self.assertEqual(conv.validators, (v2, v3, v1))

        conv = convs.Converter(v3, validators=[v2])
        self.assertEqual(conv.validators, (v2, v3))

    def test_list_converter(self):
        conv = convs.List()
        dct = OrderedDict()
        dct['1'] = 'one'
        dct['2'] = 'two'
        dct['3'] = 'three'
        self.assertEqual(conv.from_python(['one', 'two', 'three'],), dct)
        self.assertEqual(conv.to_python(dct), ['one', 'two', 'three'])
        self.assertEqual(conv.from_python(None), OrderedDict([]))
        self.assertEqual(conv.to_python({}), [])

    def test_field_block_existing_value(self):
        class f(Form):
            fields = [FieldBlock('block', fields=[Field('number', conv=convs.Int)])]
        env = AppEnvironment.create()
        form = f(env)
        field = form.fields[0]
        conv = field.conv
        form.accept({'number':'123'})
        self.assertEqual(conv._existing_value,  {'number':123})
        conv.field = None
        self.assertEqual(conv._existing_value,  {})

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

    def test_max_length(self):
        conv = convs.Char()
        self.assertIsNone(conv.max_length, None)
        conv = convs.Char(convs.length(0, 100), convs.length(10, 25))
        self.assertEqual(conv.max_length, 25)
        conv = convs.Char(convs.length(10, 25), convs.length(0, 100))
        self.assertEqual(conv.max_length, 25)


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

    def test_from_python(self):
        conv = init_conv(convs.Bool(required=True))
        self.assertEqual(conv.from_python(False), '')
        self.assertEqual(conv.from_python(True), 'checked')


class DisplayOnlyTests(unittest.TestCase):

    def test_accept_true(self):
        class f(Form):
            fields = [Field('readonly',
                            conv=convs.DisplayOnly())]
        form = f(initial={'readonly': 'init'})
        form.accept(MultiDict({'readonly': 'value'}))

        self.assertEqual(form.errors, {})
        self.assertEqual(form.python_data, {'readonly': 'init'})


class DateTests(unittest.TestCase):

    def test_to_python(self):
        '''Date converter to_python method'''
        conv = init_conv(convs.Date(format="%d.%m.%Y"))
        self.assertEqual(conv.accept('31.01.1999'), date(1999, 1, 31))
        self.assertEqual(conv.field.form.errors, {})

        self.assertRaises(convs.ValidationError, conv.to_python,
                          '30.02.2009')

    def test_readable_format(self):
        '''Ensure that readable format string for DateTime conv is generated correctly'''
        conv = init_conv(convs.Date(format="%d.%m.%Y"))
        self.assertEqual(conv.readable_format, 'DD.MM.YYYY')
        self.assertEqual(conv.accept('31'), None)
        self.assertIn(conv.readable_format, conv.field.form.errors['name'])

    def test_from_python(self):
        '''Date converter from_python method'''
        conv = init_conv(convs.Date(format="%d.%m.%Y"))
        self.assertEqual(conv.from_python(date(1999, 1, 31)), '31.01.1999')

    def test_from_python_pre_1900(self):
        # XXX move this tests to tests.utils.dt
        '''Test if from_python works fine with dates under 1900'''
        conv = init_conv(convs.Date(format="%d.%m.%Y"))
        self.assertEqual(conv.from_python(date(1899, 1, 31)), '31.01.1899')
        self.assertEqual(conv.from_python(date(401, 1, 31)), '31.01.401')

        conv = init_conv(convs.Date(format="%d.%m.%y"))
        # XXX is it right?
        self.assertEqual(conv.from_python(date(1899, 1, 31)), '31.01.99')
        self.assertEqual(conv.from_python(date(5, 1, 31)), '31.01.05')

    def test_accept_nontext(self):
        '''Date converter to_python method accepting non-text characters'''
        conv = init_conv(convs.Date(format="%d.%m.%Y"))
        self.assertEqual(conv.accept(u'\uFFFE31.01.1999\x00'), date(1999, 1, 31))
        self.assertEqual(conv.field.form.errors, {})


class TimeTests(unittest.TestCase):

    def test_from_python(self):
        '''Time converter from_python method'''
        conv = init_conv(convs.Time)
        self.assertEqual(conv.from_python(time(12, 30)), '12:30')
        self.assertEqual(conv.field.form.errors, {})

    def test_to_python(self):
        '''Time converter to_python method'''
        conv = init_conv(convs.Time)
        self.assertEqual(conv.accept('12:30'), time(12, 30))
        self.assertEqual(conv.field.form.errors, {})

        self.assertRaises(convs.ValidationError, conv.to_python,
                          '42:30')

    def test_accept_nontext(self):
        '''Time converter to_python method'''
        conv = init_conv(convs.Time)
        self.assertEqual(conv.accept(u'\x0012:\uFFFE30'), time(12, 30))
        self.assertEqual(conv.field.form.errors, {})


class DatetimeTests(unittest.TestCase):

    def test_from_python(self):
        '''Time converter from_python method'''
        conv = init_conv(convs.Datetime)
        self.assertEqual(conv.from_python(datetime(2012, 4, 5, 12, 30)),
                         '05.04.2012, 12:30')

    def test_to_python(self):
        '''Time converter to_python method'''
        conv = init_conv(convs.Datetime)
        self.assertEqual(conv.accept('05.04.2012, 12:30'),
                         datetime(2012, 4, 5, 12, 30))
        self.assertEqual(conv.field.form.errors, {})

        self.assertRaises(convs.ValidationError, conv.to_python,
                          '40.04.2012, 12:30')


class SplitDateTimeTests(unittest.TestCase):

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

        env = AppEnvironment.create()
        form = Form(env)
        form.accept(MultiDict({'dt.date': '',
                               'dt.time': '13:32'}))
        self.assertEqual(form.errors.keys(), ['dt'])

        form = Form(env)
        form.accept(MultiDict({'dt.date': '24.03.2013',
                               'dt.time': ''}))
        self.assertEqual(form.errors.keys(), ['dt'])

    def test_back(self):
        conv = init_conv(convs.SplitDateTime)
        now = datetime.now()
        self.assertEqual(conv.to_python(conv.from_python(now)), now)


class PasswordConvTests(unittest.TestCase):

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
        env = AppEnvironment.create()
        form = Form(env)

        form.accept(MultiDict({'pass.pass': '123123',
                               'pass.conf': '123'}))
        self.assertEqual(form.python_data, {'pass': None})
        self.assertEqual(form.errors.keys(), ['pass'])

    def test_required(self):
        Form = self.get_form(required=True)

        env = AppEnvironment.create()
        form = Form(env)
        form.accept(MultiDict({'pass.pass': '',
                               'pass.conf': ''}))
        self.assertEqual(form.errors.keys(), ['pass'])


class HtmlTests(unittest.TestCase):

    def test_accept(self):
        conv = convs.Html()
        value = conv.accept('<p>Hello!</p> <script>alert("Hello!")</script>')
        self.assertEqual(value, '<p>Hello!</p> ')

    def test_tune_object(self):
        conv = convs.Html(allowed_elements=['p', 'strong'])

        self.assertEqual(set(conv.cleaner.allow_tags),
                         set(['p', 'strong']))

        conv = conv(add_allowed_elements=['p', 'em'])

        self.assertEqual(set(conv.cleaner.allow_tags),
                         set(['p', 'strong', 'em']))

    def test_tune_classes(self):
        class MyHtml(convs.Html):
            allowed_elements = ['p', 'strong']

        class MyHtml2(MyHtml):
            add_allowed_elements = ['p', 'em']

        conv = MyHtml2(add_allowed_elements=['span'])

        self.assertEqual(set(conv.cleaner.allow_tags),
                         set(['p', 'strong', 'em', 'span']))

        class MyHtml3(MyHtml2):
            allowed_elements = ['a', 'b']

        conv = MyHtml3(add_allowed_elements=['span'])
        self.assertEqual(set(conv.cleaner.allow_tags),
                         set(['a', 'b', 'span']))

        class MyHtml4(convs.Html):
            allowed_elements = convs.Html.Nothing

        class MyHtml5(MyHtml4):
            add_allowed_elements = ['span']
        conv = MyHtml5()
        self.assertEqual(set(conv.cleaner.allow_tags),
                         set(['span']))

    def test_tune_class(self):
        class MyHtml(convs.Html):
            allowed_elements = ['p', 'strong']
            add_allowed_elements = ['p', 'em']

        conv = MyHtml(add_allowed_elements=['span'])
        self.assertEqual(set(conv.cleaner.allow_tags),
                         set(['p', 'strong', 'em', 'span']))

    def test_clean_value(self):
        class MyHtml(convs.Html):
            wrap_inline_tags = False
            allowed_elements = ['p', 'strong']

        conv = MyHtml()
        html = '<p>first</p><div>second</div><strong>third</strong>'
        self.assertEqual(conv.clean_value(html),
                         '<p>first</p>second<strong>third</strong>')

    #def test_tune_basic(self):
    #    'tune property not set in convs.Html'

    #    class MyHtml(convs.Html):
    #        add_allowed_css_properties = ['prop1']

    #    conv = MyHtml(add_allowed_css_properties=['prop2'])

    #    self.assertEqual(set(conv.sanitizer.kwargs['allowed_css_properties']),
    #                     set(['prop1', 'prop2']))

    def test_validators(self):
        conv = init_conv(convs.Html(convs.length(100, 1000)))

        self.assertEqual(conv.accept('<p>Hello!</p>'), None)
        self.assertEqual(conv.field.form.errors.keys(), [conv.field.name])

    def test_tag_wrapping(self):
        conv = init_conv(convs.Html(wrap_inline_tags=True,
                                    tags_to_wrap=['b', 'i']))
        cleaner = conv.cleaner
        self.assertEqual(cleaner.wrap_inline_tags, True)
        self.assertEqual(cleaner.tags_to_wrap, ['b', 'i'])

class ValidatorTests(unittest.TestCase):

    def test_length(self):
        conv = init_conv(convs.Char(convs.length(2, 4)))

        self.assertEqual(conv.accept('11'), '11')
        self.assertEqual(conv.field.form.errors, {})

        self.assertEqual(conv.accept('1111'), '1111')
        self.assertEqual(conv.field.form.errors, {})

        self.assertEqual(conv.accept(''), '')
        self.assertEqual(conv.field.form.errors, {})

        self.assertEqual(conv.accept('1'), None)
        self.assertEqual(conv.field.form.errors.keys(), [conv.field.name])
        conv.field.form.errors = {}

        self.assertEqual(conv.accept('1'*5), None)
        self.assertEqual(conv.field.form.errors.keys(), [conv.field.name])
        conv.field.form.errors = {}

        conv = init_conv(convs.Char(convs.length(2, 2)))
        self.assertEqual(conv.accept('11'), '11')
        self.assertEqual(conv.accept('1'), None)
        self.assertEqual(conv.accept('111'), None)

    def test_between(self):
        conv = init_conv(convs.Int(convs.between(2, 4)))

        self.assertEqual(conv.accept('2'), 2)
        self.assertEqual(conv.field.form.errors, {})

        self.assertEqual(conv.accept('4'), 4)
        self.assertEqual(conv.field.form.errors, {})

        self.assertEqual(conv.accept(''), None)
        self.assertEqual(conv.field.form.errors, {})

        self.assertEqual(conv.accept('0'), None)
        self.assertEqual(conv.field.form.errors.keys(), [conv.field.name])
        conv.field.form.errors = {}

        self.assertEqual(conv.accept('5'), None)
        self.assertEqual(conv.field.form.errors.keys(), [conv.field.name])
        conv.field.form.errors = {}


if __name__=='__main__':
    unittest.main()
