# -*- coding: utf-8 -*-
import unittest
from copy import copy

from iktomi.forms import *
from webob.multidict import MultiDict


class FieldTests(unittest.TestCase):

    def test_accept(self):
        'Method accept of bound field returns cleaned value'
        class _Form(Form):
            fields=[Field('input', convs.Char())]
        form = _Form()
        self.assert_(form.accept(MultiDict(input='value')))
        self.assertEqual(form.python_data['input'], 'value')

    def test_get_field(self):
        class F(Form):
            fields = [
                FieldSet('fieldset', fields=[
                    FieldList('fieldlist',
                        field=FieldSet(None, fields=[
                            Field('subfield')
                        ])
                    )
                ]),
                FieldBlock('field block', [
                    Field('blocksubfield')
                ], name='block')
            ]

        form = F()
        for nm, cls in [('fieldset', FieldSet),
                        ('fieldset.fieldlist', FieldList),
                        ('fieldset.fieldlist.1', FieldSet),
                        ('fieldset.fieldlist.1.subfield', Field),
                        ('block', FieldBlock),
                        ('blocksubfield', Field),
                        ]:
            self.assert_(isinstance(form.get_field(nm), cls),
                         '%s is not instance of %s' % (nm, cls))
            self.assertEqual(form.get_field(nm).input_name, nm)

        nm, cls = ('block.blocksubfield', Field)
        self.assert_(isinstance(form.get_field(nm), cls),
                     '%s is not instance of %s' % (nm, cls))
        self.assertEqual(form.get_field(nm).input_name,
                         'blocksubfield')

    def test_accept_multiple(self):
        class F(Form):
            fields = [
                Field('name', conv=convs.ListOf(convs.Int))
            ]

        form = F()
        form.accept(MultiDict([('name', '1'), ('name', '2')]))
        self.assertEqual(form.python_data['name'], [1, 2])

    def test_from_python_multiple(self):
        class F(Form):
            fields = [
                Field('name', conv=convs.ListOf(convs.Int),
                      initial=[1,2])
            ]

        form = F()
        self.assertEqual(form.raw_data,
                         MultiDict([('name', '1'), ('name', '2')]))

    def test_obsolete(self):
        self.assertRaises(TypeError, Field, 'name', default=1)


class FieldBlockTests(unittest.TestCase):

    def test_initial(self):
        class _Form(Form):
            fields=[
                FieldBlock('field block', [
                    Field('number', convs.Int())
                ]),
            ]
        form = _Form(initial={'number': 3})
        self.assertEqual(form.raw_data, MultiDict([('number', '3')]))
        self.assertEqual(form.python_data, {'number': 3})

    def test_accept(self):
        class _Form(Form):
            fields=[
                FieldBlock('field block', [
                    Field('number', convs.Int())
                ]),
            ]
        form = _Form()
        self.assertEqual(form.raw_data, MultiDict([('number', '')]))
        self.assertEqual(form.python_data, {'number': None})
        self.assert_(form.accept({'number': '4'}))
        self.assertEqual(form.python_data, {'number': 4})
        self.assertEqual(form.get_field('number').raw_value, '4')
        self.assertEqual(form.errors, {})
