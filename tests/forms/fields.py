# -*- coding: utf-8 -*-
import unittest
from webob import Request
from iktomi.forms import Form, FieldSet, FieldList, FieldBlock, Field, \
            FileField, convs
from iktomi.web.app import AppEnvironment

from webob.multidict import MultiDict


class FieldTests(unittest.TestCase):

    def test_accept(self):
        'Method accept of bound field returns cleaned value'
        class _Form(Form):
            fields=[Field('input', convs.Char())]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assert_(form.accept(MultiDict(input='value')))
        self.assertEqual(form.python_data['input'], 'value')

    def test_id(self):
        class _Form(Form):
            fields=[Field('input', convs.Char())]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assertEqual(form.get_field('input').id, 'input')
        form.id = 'myform'
        self.assertEqual(form.get_field('input').id, 'myform-input')

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

        env = AppEnvironment.create()
        form = F(env)
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

        env = AppEnvironment.create()
        form = F(env)
        form.accept(MultiDict([('name', '1'), ('name', '2')]))
        self.assertEqual(form.python_data['name'], [1, 2])

    def test_from_python_multiple(self):
        class F(Form):
            fields = [
                Field('name', conv=convs.ListOf(convs.Int),
                      initial=[1,2])
            ]

        env = AppEnvironment.create()
        form = F(env)
        self.assertEqual(form.raw_data,
                         MultiDict([('name', '1'), ('name', '2')]))

    def test_obsolete(self):
        self.assertRaises(TypeError, Field, 'name', default=1)

    def test_check_value_type(self):
        '''Pass file value to ordinary Field'''
        class F(Form):
            fields = [Field('inp')]
        request = Request.blank('/', POST=dict(inp=('foo.txt', 'ggg')))
        env = AppEnvironment.create()
        form = F(env)
        self.assertEqual(form.accept(request.POST), False)
        self.assertEqual(form.errors.keys(), ['inp'])

    def test_clean_value(self):
        class AssertConv(convs.Int):
            def to_python(conv, value):
                value = convs.Int.to_python(conv, value)
                if value is not None:
                    field = conv.field.form.get_field('num')
                    self.assertEqual(field.clean_value, value)
                return value

        class F(Form):
            fields = [FieldBlock('', fields=[
                          Field('num',
                                conv=convs.Int()),
                          Field('f2',
                                conv=AssertConv())
                          ])]

        env = AppEnvironment.create()
        form = F(env)
        self.assertEqual(form.get_field('num').clean_value, None)

        form = F(env, initial={'num': 2})
        self.assertEqual(form.get_field('num').clean_value, 2)

        form = F(env)
        form.accept({'num': '4', 'f2': '4'})
        self.assertEqual(form.get_field('num').clean_value, 4)
        self.assertEqual(form.get_field('f2').clean_value, 4)


class FieldBlockTests(unittest.TestCase):

    def test_initial(self):
        class _Form(Form):
            fields=[
                FieldBlock('field block', [
                    Field('number', convs.Int())
                ]),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'number': 3})
        self.assertEqual(form.raw_data, MultiDict([('number', '3')]))
        self.assertEqual(form.python_data, {'number': 3})
        self.assertEqual(form.get_field('number').clean_value, 3)

    def test_accept(self):
        class _Form(Form):
            fields=[
                FieldBlock('field block', [
                    Field('number', convs.Int())
                ]),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assertEqual(form.raw_data, MultiDict([('number', '')]))
        self.assertEqual(form.python_data, {'number': None})
        self.assert_(form.accept({'number': '4'}))
        self.assertEqual(form.python_data, {'number': 4})
        self.assertEqual(form.get_field('number').raw_value, '4')
        self.assertEqual(form.errors, {})

    def test_fieldblock_in_fieldset(self):
        class _Form(Form):
            fields=[FieldSet('fs', fields=[
                FieldBlock('field block', [
                    Field('number', convs.Int())
                ]),
            ])]
        env = AppEnvironment.create()
        form = _Form(env, initial={'fs':{'number': 5}})
        self.assertEqual(form.raw_data, MultiDict([('fs.number', '5')]))
        self.assertEqual(form.python_data, {'fs': {'number': 5}})
        self.assert_(form.accept({'fs.number': '4'}))
        self.assertEqual(form.python_data, {'fs': {'number': 4}})
        self.assertEqual(form.get_field('fs.number').raw_value, '4')
        self.assertEqual(form.errors, {})



    def test_validation_error(self):
        def validator(conv, value):
            raise convs.ValidationError(by_field={'number': 'error'})
        class _Form(Form):
            fields=[
                FieldBlock('field block', [
                    Field('number', convs.Int())
                ],
                conv=FieldBlock.conv(validator)),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assert_(not form.accept({'number': '4'}))
        self.assertEqual(form.python_data, {'number': None})
        self.assertEqual(form.get_field('number').raw_value, '4')
        self.assertEqual(form.get_field('number').error, 'error')

    def test_nested(self):
        class _Form(Form):
            fields=[
                FieldBlock('field block', [
                    Field('number', convs.Int()),
                    FieldBlock('field block', [
                        Field('title', convs.Char()),
                    ]),
                ]),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assertEqual(form.raw_data, MultiDict([('number', ''),
                                                   ('title', '')]))
        self.assertEqual(form.python_data, {'number': None,
                                            'title': None})
        self.assert_(form.accept({'number': '4', 'title': 'Hello'}),
                     form.errors)
        self.assertEqual(form.python_data, {'number': 4,
                                            'title': 'Hello'})
        self.assertEqual(form.get_field('number').raw_value, '4')
        self.assertEqual(form.get_field('title').raw_value, 'Hello')
        self.assertEqual(form.errors, {})

    def test_fieldblock_readonly(self):
        class _Form(Form):
            fields=[
                FieldBlock('field block',
                           fields=[
                                    Field('number',
                                          convs.Int()),
                                    Field('title',
                                          convs.Char()),
                                  ],
                           permissions='r'),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assertEqual(form.raw_data, MultiDict([('number', ''),
                                                   ('title', '')]))
        self.assertEqual(form.python_data, {'number': None,
                                            'title': None})
        self.assert_(form.accept({'number': '4', 'title': 'Hello'}),
                     form.errors)
        self.assertEqual(form.python_data, {'number': None,
                                            'title': None})
        self.assertEqual(form.get_field('number').raw_value, '')
        self.assertEqual(form.get_field('title').raw_value, '')
        self.assertEqual(form.errors, {})



class FileFieldTests(unittest.TestCase):

    def test_accept(self):
        class _Form(Form):
            fields=[FileField('inp')]
        env = AppEnvironment.create()
        form = _Form(env)
        request = Request.blank('/', POST=dict(inp=('file.txt', 'ggg')))
        self.assert_(form.accept(request.POST),
                     form.errors)
        self.assertEqual(form.python_data['inp'].file.read(), 'ggg')

    def test_check_value_type(self):
        '''Pass string value to FileField'''
        class F(Form):
            fields = [FileField('inp')]
        request = Request.blank('/', POST=dict(inp='ggg'))
        form = F()
        self.assertEqual(form.accept(request.POST), False)
        self.assertEqual(form.errors.keys(), ['inp'])
