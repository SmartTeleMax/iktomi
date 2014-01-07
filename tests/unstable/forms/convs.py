# -*- coding: utf-8 -*-

import unittest

from iktomi.forms import *
from iktomi.unstable.forms import convs


def init_conv(conv, name='name'):
    class F(Form):
        fields = [Field(name, conv)]
    return F().get_field(name).conv




class EmailConvTests(unittest.TestCase):

    def test_email(self):
        conv = init_conv(convs.Email)
        email = '-!#$%&\'*+/=?^_`{}.a0@example.com'
        value = conv.accept(email)
        self.assertEqual(value, email)

    def test_strip(self):
        conv = init_conv(convs.Email)
        # Vertical tab ('\v' or '\xob') is whitespace too, but it's not safe
        # for XML and HTML, so it's replaced.
        value = conv.accept(' \t\r\nname@example.com \t\r\n')
        self.assertEqual(value, u'name@example.com')

    def test_non_text(self):
        for c in u'\x00\x08\x0B\x0C\x0E\x0F\uD800\uDFFF':
            conv = init_conv(convs.Email)
            value = conv.accept(u'name@example.com'+c)
            self.assertEqual(value, None)
            self.assertEqual(conv.field.form.errors.keys(), [conv.field.name])

    def test_invalid(self):
        for email in ['name@com',
                      '@example.com',
                      'example.com',
                      'name@127.0.0.1',
                      'name@example.i',
                      'name@example.123',
                      '.name@example.com',
                      'name.@example.com',
                      'na..me@example.com']:
            conv = init_conv(convs.Email)
            value = conv.accept('name@com')
            self.assertEqual(value, None)
            self.assertEqual(conv.field.form.errors.keys(), [conv.field.name])


class ModelDictConvTests(unittest.TestCase):

    def _init_modeldict_conv(self, *a, **kw):
        class M(object):
            a = b = None
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        kw['model'] = M

        class F(Form):
            fields = [
                FieldSet('fs',
                         conv=convs.ModelDictConv(*a, **kw),
                         fields=[Field('a'), Field('b')]),
            ]
        return F().get_field('fs').conv

    def test_to_python(self):
        conv = self._init_modeldict_conv()
        obj = conv.to_python({'a': 1, 'b': '2', 'c': 3})
        self.assertEqual(obj.a, 1)
        self.assertEqual(obj.b, '2')
        self.assertFalse(hasattr(obj, 'c'))

    def test_validation_error(self):
        def validate(field, value):
            raise convs.ValidationError('')
        conv = self._init_modeldict_conv(validate)
        obj = conv.accept({'a': 1, 'b': '2', 'c': 3})
        self.assertEqual(obj.__class__.__name__, 'M')
        self.assertEqual(obj.a, None)
        self.assertEqual(obj.b, None)
        self.assertFalse(hasattr(obj, 'c'))

    def test_from_python(self):
        conv = self._init_modeldict_conv()
        obj = conv.model(a=1, b='2', c=3)
        value = conv.from_python(obj)
        self.assertEqual(value, {'a': 1, 'b': '2'})
