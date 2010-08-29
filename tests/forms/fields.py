# -*- coding: utf-8 -*-
import unittest
from copy import copy

from insanities.forms import *
from insanities.web.core import RequestContext
from webob.multidict import MultiDict

from .testutils import FormTestCase, MockForm


class FieldTests(FormTestCase):

    def test_accept(self):
        'Method accept of bound field returns cleaned value'
        field = MockForm(Field('input', conv=convs.Char), 
                env=self.env(), 
                data=MultiDict(input='value')).fields[0]
        self.assertEqual(field.accept(), 'value')

    def test_accept_invalid(self):
        'Method accept of bound field returns cleaned value'
        field = MockForm(Field('input', conv=convs.Char(required=True)), 
                env=self.env(), 
                data=MultiDict()).fields[0]
        self.assertRaises(convs.ValidationError, field.accept)

    def test_render(self):
        'Method render of bound field'
        field = MockForm(Field('input', conv=convs.Char), 
                env=self.env(), 
                data=MultiDict(input='value')).fields[0]
        self.assertEqual(field.render(), ('textinput', {'field': field.widget.field, 
                                                        'readonly': False, 
                                                        'widget': field.widget, 
                                                        'value': 'value'}))

    def test_render_readonly(self):
        'Method render of bound field'
        field = MockForm(Field('input', conv=convs.Char), 
                permissions=set('r'),
                env=self.env(), 
                data=MultiDict(input='value')).fields[0]
        self.assertEqual(field.render(), ('textinput', {'field': field.widget.field, 
                                                        'readonly': True, 
                                                        'widget': field.widget, 
                                                        'value': 'value'}))
