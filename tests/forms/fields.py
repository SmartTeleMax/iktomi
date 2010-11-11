# -*- coding: utf-8 -*-
import unittest
from copy import copy

from insanities.forms import *
from insanities.web.core import RequestContext
from webob.multidict import MultiDict


class FieldTests(unittest.TestCase):

    def test_accept(self):
        'Method accept of bound field returns cleaned value'
        class _Form(Form):
            fields=[Field('input', convs.Char())]
        form = _Form()
        self.assert_(form.accept(MultiDict(input='value')))
        self.assertEqual(form.python_data['input'], 'value')

    def test_accept_invalid(self):
        'Method accept of bound field returns cleaned value'

        class _Form(Form):
            fields=[Field('input', convs.Char(required=True))]

        field = _Form().fields[0]
        self.assertRaises(convs.ValidationError, field.accept)
