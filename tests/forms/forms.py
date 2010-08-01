# -*- coding: utf-8 -*-
import unittest
from copy import copy

from insanities.forms import *
from webob.multidict import MultiDict
from .testutils import FormTestCase


class TestForm(FormTestCase):
    def test_init(self):
        class SampleForm(Form):
            fields=[
                Field('input'),
                Field('input2'),
                Field('int', conv=convs.Int, default=10),
                Field('input3', default='abyr'),
            ]

        form = SampleForm(self.env(), initial={
            'input2': '123',
            'input3': '123',
        })

        self.assertEqual(form.data, MultiDict([
            ('input', ''),
            ('input2', '123'),
            ('input3', '123'),
            ('int', '10'),
        ]))

        self.assertEqual(form.python_data, {
            'input': None,
            'input2': '123',
            'input3': '123',
            'int': 10,
        })

    def test_name(self):
        class SampleForm(Form):
            fields=[Field('input')]

        form = SampleForm(self.env(), name='formname')

        self.assertEqual(form.get_field('input').input_name, 'formname:input')

    def test_permissions(self):
        class SampleForm(Form):
            fields=[Field('input')]

        form = SampleForm(self.env(), permissions='rw')
        self.assertEqual(form.permissions, set('rw'))

        class SampleForm(Form):
            permissions='rwx'
            fields=[Field('input')]

        form = SampleForm(self.env())
        self.assertEqual(form.permissions, set('rwx'))

    def test_get_data(self):
        class SampleForm(Form):
            fields=[Field(name='input'),
                    Field(name='input2'),
                    ]

        form = SampleForm(self.env())
        data = MultiDict([
            ('input', ''),
            ('input2', '123'),
        ])
        form.accept(data)

        self.assertEqual(form.get_data(compact=False), MultiDict([
            ('input', ''),
            ('input2', '123'),
        ]))
        self.assertEqual(form.get_data(compact=True), MultiDict([
            ('input2', '123'),
        ]))


    def test_render(self):
        class SampleForm(Form):
            fields=[Field(name='input1'),
                    Field(name='input2'),
                    ]

        f = SampleForm(self.env())
        template_name, data = f.render()
        self.assert_(f in data.values())

    def test_is_valid(self):
        class SampleForm(Form):
            fields=[Field('input', conv=convs.Int)]

        form = SampleForm(self.env())

        form.accept(MultiDict([('input', '123')]))
        self.assert_(form.is_valid)

        form = SampleForm(self.env())
        form.accept(MultiDict([('input', 'NaN')]))
        self.assert_(not form.is_valid)

    def test_accept_valid(self):
        class SampleForm(Form):
            fields=[Field(name='input1', conv=convs.Int),
                    Field(name='input2', conv=convs.Int,
                                 default=25,
                                 perm_getter=perms.SimplePerm('r')),
                    ]
        frm = SampleForm(self.env())
        assert frm.accept(MultiDict([('input1', '123'), ('input2', 1),]))

        assert not frm.errors
        self.assertEqual(frm.python_data, {'input1': 123, 'input2': 25})
        self.assertEqual(frm.data, {'input1': '123', 'input2': '25'})

    def test_accept_invalid(self):
        class SampleForm(Form):
            fields=[Field(name='input1',
                                 conv=convs.Int,
                                 default=1)]

        frm = SampleForm(self.env())
        assert not frm.accept(MultiDict([('input1', '12m')]))

        assert frm.errors
        self.assertEqual(frm.python_data, {'input1': 1})
        self.assertEqual(frm.data, MultiDict([('input1', '12m')]))

    def test_accept_invalid_nested(self):
        class SampleForm(Form):
            fields=[FieldSet(
                        name='fieldset',
                        fields=[
                              Field(name='input2', conv=convs.Int),
                            ]),
                    Field(name='input1', conv=convs.Int),
                    ]

        frm = SampleForm(self.env())
        md = MultiDict([
            ('fieldset.input2', '12c'),
            ('input1', '20'),
            ])
        assert not frm.accept(md)
        assert frm.errors

        self.assertEqual(frm.python_data['input1'], 20)
        self.assertEqual(frm.data, md)

    def test_accept_clean_interface_valid(self):
        class SampleForm(Form):
            fields=[Field(name='input1', conv=convs.Int),
                    Field(name='input2', conv=convs.Int)]

            def clean__input2(self, value):
                if value != self.python_data['input1']:
                    raise convs.ValidationError('')
                return value

        frm = SampleForm(self.env())
        assert frm.accept(MultiDict([('input1', '12'), ('input2', '12')]))
        assert not frm.errors

        self.assertEqual(frm.python_data, {'input1': 12, 'input2': 12})

    def test_accept_clean_interface_invalid(self):
        class SampleForm(Form):
            fields=[Field(name='input1', conv=convs.Int),
                    Field(name='input2', conv=convs.Int)]

            def clean__input2(self, value):
                if value != self.python_data['input1']:
                    raise convs.ValidationError('')
                return value

        frm = SampleForm(self.env())
        assert not frm.accept(MultiDict([('input1', '12'), ('input2', '13')]))
        assert frm.errors

        self.assertEqual(frm.python_data, {'input1': 12})


    def get_field(self):
        class SampleForm(Form):
            fields=[FieldSet(
                        name='fieldset',
                        fields=[
                              Field(name='input2', conv=convs.Int),
                            ]),
                    Field(name='input1', conv=convs.Int),
                    ]
        self.assertEqual(self.get_field('input1').input_name, 'input1')
        self.assertEqual(self.get_field('fieldset.input2').input_name, 'input2')
        self.assertEqual(self.get_field('field'), None)


if __name__ == '__main__':
    unittest.main()
