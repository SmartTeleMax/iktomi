# -*- coding: utf-8 -*-

import unittest

from iktomi.forms import *
from iktomi.forms.convs import ValidationError


def init_field(name='name'):
    class f(Form):
        fields = [Field(name)]
    return f().get_field(name)

class ValidationErrorTests(unittest.TestCase):

    def test_repr(self):
        r = "%r" % ValidationError(u'Ошибка error', {'.field': u'Ошибка'})
        self.assert_('error' in r)
        self.assert_('.field' in r)

    def test_message(self):
        field = init_field()
        form = field.form

        ve = ValidationError(u'Ошибка')

        ve.fill_errors(field)
        self.assertEqual(form.errors, {'name': u'Ошибка'})

    def test_by_field_field_list(self):
        class f(Form):
            fields = [FieldList('name',
                field=FieldSet(None, fields=[
                    Field('subfield')
                ])
            )]
        form = f()

        ve = ValidationError(by_field={'.2.subfield': u'Ошибка-2',
                                       'field': u'Ошибка-3',
                                       # XXX what does this mean?
                                       '': u'Ошибка-4'}) 

        ve.fill_errors(form.get_field('name'))
        self.assertEqual(form.errors, {'name-2.subfield': u'Ошибка-2',
                                       'field': u'Ошибка-3',
                                       '': u'Ошибка-4'})

    def test_by_field_fieldset(self):
        class f(Form):
            fields = [
                FieldSet('name', fields=[
                    Field('subfield')
                ])
            ]
        form = f()

        ve = ValidationError(by_field={'.subfield': u'Ошибка-1',
                                       'field': u'Ошибка-3',
                                       # XXX what does this mean?
                                       '': u'Ошибка-4'}) 

        ve.fill_errors(form.get_field('name'))
        self.assertEqual(form.errors, {'name.subfield': u'Ошибка-1',
                                       'field': u'Ошибка-3',
                                       '': u'Ошибка-4'})

        ve = ValidationError(by_field={'.absent': u'1'})
        self.assertRaises(AttributeError, # XXX is AttributeError good?
                          lambda: ve.fill_errors(form.get_field('name')))

    def test_by_field_up(self):
        class f(Form):
            fields = [
                FieldSet('name', fields=[
                    Field('subfield'),
                    Field('another')
                ]),
                Field('other')
            ]
        form = f()

        ve = ValidationError(by_field={'..another': u'1',
                                       '...other': u'2'})

        ve.fill_errors(form.get_field('name.subfield'))
        self.assertEqual(form.errors, {'name.another': u'1',
                                       'other': u'2'})

        ve = ValidationError(by_field={'...other': u'1'})
        self.assertRaises(AttributeError, 
                          lambda: ve.fill_errors(form.get_field('name')))
