# -*- coding: utf-8 -*-

import unittest

from iktomi.forms import *
from iktomi.unstable.forms import convs


def init_conv(conv, name='name'):
    class f(Form):
        fields = [Field(name, conv)]
    return f().get_field(name).conv


class ConverterTests(unittest.TestCase):

    def test_email(self):
        conv = init_conv(convs.Email)
        email = '-!#$%&\'*+/=?^_`{}.a0@example.com'
        value = conv.accept(email)
        self.assertEqual(value, email)

    def test_email_strip(self):
        conv = init_conv(convs.Email)
        # Vertical tab ('\v' or '\xob') is whitespace too, but it's not safe
        # for XML and HTML, so it's replaced.
        value = conv.accept(' \t\r\nname@example.com \t\r\n')
        self.assertEqual(value, u'name@example.com')

    def test_email_non_text(self):
        for c in u'\x00\x08\x0B\x0C\x0E\x0F\uD800\uDFFF':
            conv = init_conv(convs.Email)
            value = conv.accept(u'name@example.com'+c)
            self.assertEqual(value, None)
            self.assertEqual(conv.field.form.errors.keys(), [conv.field.name])

    def test_email_invalid(self):
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
