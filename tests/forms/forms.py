# -*- coding: utf-8 -*-
import unittest
from copy import copy

from insanities.forms import fields, convs, form, widgets, media, perms


class TestFormClass(unittest.TestCase):
    @property
    def env(self):
        from os import path
        import jinja2
        from insanities.ext import jinja2 as jnj

        DIR = jnj.__file__
        DIR = path.dirname(path.abspath(DIR))
        TEMPLATES = [path.join(DIR, 'templates')]

        template_loader = jinja2.Environment(
                            loader=jinja2.FileSystemLoader(TEMPLATES))
        return jnj.FormEnvironment(template_loader)

class TestForm(TestFormClass):
    def test_init(self):
        class SampleForm(form.Form):
            fields=[fields.Field(name='input'),
                    fields.Field(name='input2'),
                    fields.Field(conv=convs.Int,
                                 name='int', default=10),
                    fields.Field(name='input3', default='abyr'),
                    ]

        frm = SampleForm(self.env, initial={
            'input2': '123',
            'input3': '123',
        })

        self.assertEqual(frm.data, form.MultiDict([
            ('input', ''),
            ('input2', '123'),
            ('input3', '123'),
            ('int', '10'),
        ]))
        self.assertEqual(frm.python_data, {
            'input': None,
            'input2': '123',
            'input3': '123',
            'int': 10,
        })

    def test_name(self):
        class SampleForm(form.Form):
            fields=[fields.Field(name='input')]
        frm = SampleForm(self.env, name='formname')

        self.assertEqual(frm.get_field('input').input_name, 'formname:input')

    def test_permissions(self):
        class SampleForm(form.Form):
            fields=[fields.Field(name='input')]

        frm = SampleForm(self.env, permissions='rw')
        self.assertEqual(frm.permissions, set('rw'))

        class SampleForm(form.Form):
            permissions='rw'
            fields=[fields.Field(name='input')]

        frm = SampleForm(self.env)
        self.assertEqual(frm.permissions, set('rw'))

    def test_get_data(self):
        class SampleForm(form.Form):
            fields=[fields.Field(name='input'),
                    fields.Field(name='input2'),
                    ]

        frm = SampleForm(self.env)
        data = form.MultiDict([
            ('input', ''),
            ('input2', '123'),
        ])
        frm.accept(data)

        self.assertEqual(frm.get_data(compact=False), form.MultiDict([
            ('input', ''),
            ('input2', '123'),
        ]))
        self.assertEqual(frm.get_data(compact=True), form.MultiDict([
            ('input2', '123'),
        ]))


    def test_render(self):
        class SampleForm(form.Form):
            fields=[fields.Field(name='input1'),
                    fields.Field(name='input2'),
                    ]

        # XXX how to test render?
        rnd = SampleForm(self.env).render()
        assert 'input1' in rnd and 'input2' in rnd

    def test_is_valid(self):
        class SampleForm(form.Form):
            fields=[fields.Field(name='input', conv=convs.Int)]

        frm = SampleForm(self.env)

        # XXX not validated form returns is_valid = True
        # assert not frm.is_valid        
        frm.accept(form.MultiDict([('input', '123')]))
        assert frm.is_valid

        frm = SampleForm(self.env)
        frm.accept(form.MultiDict([('input', 'NaN')]))
        assert not frm.is_valid

    def test_get_media(self):
        pass
        #media = FormMedia(self.media, env=self.env)
        #for field in self.fields:
        #    media += field.get_media()
        #return media

    def test_accept_valid(self):
        class SampleForm(form.Form):
            fields=[fields.Field(name='input1', conv=convs.Int),
                    fields.Field(name='input2', conv=convs.Int,
                                 default=25,
                                 perm_getter=perms.SimplePerm('r')),
                    ]
        frm = SampleForm(self.env)
        assert frm.accept(form.MultiDict([('input1', '123'), ('input2', 1),]))

        assert not frm.errors
        self.assertEqual(frm.python_data, {'input1': 123, 'input2': 25})
        self.assertEqual(frm.data, {'input1': '123', 'input2': '25'})

    def test_accept_invalid(self):
        class SampleForm(form.Form):
            fields=[fields.Field(name='input1',
                                 conv=convs.Int,
                                 default=1)]

        frm = SampleForm(self.env)
        assert not frm.accept(form.MultiDict([('input1', '12m')]))

        assert frm.errors
        self.assertEqual(frm.python_data, {'input1': 1})
        self.assertEqual(frm.data, form.MultiDict([('input1', '12m')]))

    def test_accept_invalid_nested(self):
        class SampleForm(form.Form):
            fields=[fields.FieldSet(
                        name='fieldset',
                        fields=[
                              fields.Field(name='input2', conv=convs.Int),
                            ]),
                    fields.Field(name='input1', conv=convs.Int),
                    ]

        frm = SampleForm(self.env)
        md = form.MultiDict([
            ('fieldset.input2', '12c'),
            ('input1', '20'),
            ])
        assert not frm.accept(md)
        assert frm.errors

        self.assertEqual(frm.python_data['input1'], 20)
        self.assertEqual(frm.data, md)

    def test_accept_clean_interface_valid(self):
        class SampleForm(form.Form):
            fields=[fields.Field(name='input1', conv=convs.Int),
                    fields.Field(name='input2', conv=convs.Int)]

            def clean__input2(self, value):
                if value != self.python_data['input1']:
                    raise convs.ValidationError('')
                return value

        frm = SampleForm(self.env)
        assert frm.accept(form.MultiDict([('input1', '12'), ('input2', '12')]))
        assert not frm.errors

        self.assertEqual(frm.python_data, {'input1': 12, 'input2': 12})

    def test_accept_clean_interface_invalid(self):
        class SampleForm(form.Form):
            fields=[fields.Field(name='input1', conv=convs.Int),
                    fields.Field(name='input2', conv=convs.Int)]

            def clean__input2(self, value):
                if value != self.python_data['input1']:
                    raise convs.ValidationError('')
                return value

        frm = SampleForm(self.env)
        assert not frm.accept(form.MultiDict([('input1', '12'), ('input2', '13')]))
        assert frm.errors

        self.assertEqual(frm.python_data, {'input1': 12})


    def get_field(self):
        class SampleForm(form.Form):
            fields=[fields.FieldSet(
                        name='fieldset',
                        fields=[
                              fields.Field(name='input2', conv=convs.Int),
                            ]),
                    fields.Field(name='input1', conv=convs.Int),
                    ]
        self.assertEqual(self.get_field('input1').input_name, 'input1')
        self.assertEqual(self.get_field('fieldset.input2').input_name, 'input2')
        self.assertEqual(self.get_field('field'), None)


if __name__ == '__main__':
    unittest.main()
