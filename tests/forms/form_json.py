# -*- coding: utf-8 -*-

import unittest

from iktomi.forms.form_json import *
from iktomi.forms import convs
from iktomi.web.app import AppEnvironment


class FormClassInitializationTests(unittest.TestCase):

    def test_init(self):
        'Initialization of form object'
        class F(Form):
            fields=[
                Field('first', convs.Int()),
                Field('second', convs.Int()),
            ]
        env = AppEnvironment.create()
        form = F(env)
        self.assertEqual(form.initial, {})
        self.assertEqual(form.get_data(), {'first':'', 'second':''})
        self.assertEqual(form.python_data, {'first':None, 'second':None})


    def test_with_initial(self):
        'Initialization of form object with fields initial values'
        class F(Form):
            fields=[
                Field('first', convs.Int(), initial=1),
                Field('second', convs.Int(), get_initial=lambda: 2),
            ]
        env = AppEnvironment.create()
        form = F(env)
        self.assertEqual(form.initial, {})
        self.assertEqual(form.get_data(), {'first':u"1", 'second':u"2"})
        self.assertEqual(form.python_data, {'first':1, 'second':2})

    def test_with_semi_initial(self):
        'Initialization of form object with one field initial value'
        class F(Form):
            fields=[
                Field('first', convs.Int(), initial=1),
                Field('second', convs.Int()),
            ]
        env = AppEnvironment.create()
        form = F(env)
        self.assertEqual(form.initial, {})
        self.assertEqual(form.get_data(), {'first':u"1", 'second':u""})

        self.assertEqual(form.python_data, {'first':1, 'second':None})

    def test_with_initial_and_initial(self):
        'Initialization of form object with initial and initial values'
        class F(Form):
            fields=[
                Field('first', convs.Int(), initial=3),
                Field('second', convs.Int()),
            ]
        env = AppEnvironment.create()
        form = F(env, initial={'first':1, 'second':2})
        self.assertEqual(form.initial, {'first':1, 'second':2})
        self.assertEqual(form.get_data(), {'first':u'1', 'second':u'2'})
        self.assertEqual(form.python_data, {'first':1, 'second':2})

    def test_fieldset_with_initial(self):
        'Initialization of form object with fieldset with initial values'
        class _Form(Form):
            fields=[
                FieldSet('set', fields=[
                    Field('first', convs.Int()),
                    Field('second', convs.Int()),
                ]),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'set': {'first': 1, 'second': 2}})
        self.assertEqual(form.get_data(), {'set':{'first':u'1', 'second':u'2'}})
        self.assertEqual(form.python_data, {'set':{'first':1, 'second':2}})

    def test_fieldset_with_initial_and_initial(self):
        'Initialization of form object with fieldset with initial and initial values'
        class _Form(Form):
            fields=[
                FieldSet('set', fields=[
                    Field('first', convs.Int(), initial=3),
                    Field('second', convs.Int()),
                ]),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'set': {'first': None, 'second': 2}})
        self.assertEqual(form.get_data(), {'set':{'first': '', 'second': '2'}})
        self.assertEqual(form.python_data, {'set': {'first': None, 'second': 2}})

    def test_init_fieldlist_with_initial(self):
        'Initialization of form object with fieldlist with initial values'
        class _Form(Form):
            fields=[
                FieldList('list', field=Field('number', convs.Int())),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'list': [5, 6, 7]})
        # TODO: fix FieldList
        # self.assertEqual(form.get_data(), {'list':{'number-1':5,
        #                                            'number-2':6,
        #                                            'number-3':7,
        #                                            }})
        self.assertEqual(form.python_data, {'list': [5, 6, 7]})

    def test_fieldlist_with_initial_and_initial(self):
        'Initialization of form object with fieldlist with initial and initial values'
        class _Form(Form):
            fields=[
                FieldList('list', field=Field('number', convs.Int(), initial=2)),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'list': [5, 6, 7]})
        # TODO: fix FieldList
        # self.assertEqual(form.raw_data, MultiDict([('list-indices', '1'),
        #                                            ('list-indices', '2'),
        #                                            ('list.1', '1'),
        #                                            ('list.2', '2')
        #                                           ]))
        self.assertEqual(form.python_data, {'list': [5, 6, 7]})


class FormErrorsTests(unittest.TestCase):

    def test_simple(self):
        'Accept with errors'
        class _Form(Form):
            fields=[
                Field('first', convs.Int(required=True)),
                Field('second', convs.Int(required=True)),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assertTrue(not form.accept(dict(first='1')))
        self.assertEqual(form.errors, {'second': convs.Converter.error_required})

    def test_fieldset(self):
        'Accept with errors (fieldset)'
        class _Form(Form):
            fields=[
                FieldSet('set', fields=[
                    Field('first', convs.Int(), initial=1, permissions='r'),
                    Field('second', convs.Int(required=True), initial=2),
                ]),
                Field('third', convs.Int()),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assertTrue(not form.accept({'set':{'first': '2d',
                                                'second': '',},
                                         'third': '3f'}))
        self.assertEqual(form.python_data, {'set': {'first': 1,
                                                    'second': 2},
                                            'third': None})
        # TODO: check required format for errors(nested dicts or by ".") 
        self.assertEqual(form.errors, {'set.second': convs.Int.error_required,
                                       'third': convs.Int.error_notvalid})
        self.assertEqual(form.get_data(), {'set':{'first': '1',
                                                  'second': '',},
                                           'third': '3f'})

    # TODO: fix FieldList 
    def test_fieldlist_with_initial_delete(self):
        'Fieldlist element deletion'
        class _Form(Form):
            fields=[
                FieldList('list', field=Field('number', convs.Int())),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'list': [5, 6, 7]})
        self.assertEqual(form.python_data, {'list': [5, 6, 7]})
        #self.assertTrue(form.accept((('list-indices', '1'), ('list-indices', '3')), 
        #                                          **{'list.1': '1', 'list.3': '3'})))
        #self.assertEqual(form.python_data, {'list': [1, 3]})

    def test_form__clean(self):
        'Assert clean__ method existance causes errors'
        def get_form():
            class _Form(Form):
                fields=[
                    Field('first', convs.Int()),
                ]

                def clean__first(self, value):
                    pass
        self.assertRaises(TypeError, get_form)


class FormClassAcceptTests(unittest.TestCase):

    def test_accept(self):
        'Clean accept'
        class _Form(Form):
            fields=[
                Field('first', convs.Int()),
                Field('second', convs.Int()),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assertTrue(form.accept(dict(first='1', second='2')))
        self.assertEqual(form.initial, {})
        self.assertEqual(form.get_data(), {'first':'1', 'second':'2'})
        self.assertEqual(form.python_data, {'first':1, 'second':2})


    def test_with_initial(self):
        'Accept with initial values'
        class _Form(Form):
            fields=[
                Field('first', convs.Int(), initial=3),
                Field('second', convs.Int(required=False), get_initial=lambda: 4),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        form.accept(dict(first='1'))
        self.assertTrue(form.accept(dict(first='1')))
        self.assertEqual(form.initial, {})
        self.assertEqual(form.python_data, {'first':1, 'second':None})

    def test_fieldlist_is_required(self):
        'Fieldlist is required and accepted value is empty'
        class _Form(Form):
            fields=[
                FieldList('list', field=Field('number', convs.Int())),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assertEqual(form.python_data, {'list': []})
        self.assertEqual(form.get_data(), {})
        self.assert_(form.accept({}))
        self.assertEqual(form.python_data, {'list': []})
        self.assertEqual(form.errors, {})
        self.assertEqual(form.get_data(), {})

    def test_fieldset_is_required(self):
        'Fieldset is required and accepted value is empty'
        class _Form(Form):
            fields=[
                FieldSet('set', fields=[Field('number', convs.Int())]),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assertEqual(form.python_data, {'set': {'number': None}})
        self.assert_(form.accept({}))
        self.assertEqual(form.python_data, {'set': {'number': None}})
        self.assertEqual(form.get_field('set.number').raw_value, '')
        self.assertEqual(form.errors, {})
