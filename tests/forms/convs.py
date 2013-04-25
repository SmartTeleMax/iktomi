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
        value = conv.accept('name@example.com')
        self.assertEqual(value, u'name@example.com')
