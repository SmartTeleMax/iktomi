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
        self.assertEqual(form.get_data(), {'list':[{'1':'5'}, {'2':'6'}, {'3':'7'}]})
        self.assertEqual(form.python_data, {'list': [5, 6, 7]})

    def test_fieldlist_with_initial_and_initial(self):
        'Initialization of form object with fieldlist with initial and initial values'
        class _Form(Form):
            fields=[
                FieldList('list', field=Field('number', convs.Int(), initial=2)),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'list': [5, 6, 7]})
        self.assertEqual(form.get_data(), {'list':[{'1':'5'}, {'2':'6'}, {'3':'7'}]})
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
        self.assertEqual(form.errors, {'set':{'second': convs.Int.error_required},
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
        self.assertEqual(form.get_data(), {'list':[{'1':'5'}, {'2':'6'}, {'3':'7'}]})
        self.assertEqual(form.python_data, {'list': [5, 6, 7]})

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
        self.assertEqual(form.get_data(), {'list':[]})
        self.assert_(form.accept({}))
        self.assertEqual(form.python_data, {'list': []})
        self.assertEqual(form.errors, {})
        self.assertEqual(form.get_data(), {'list':[]})

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
        self.assertEqual(form.get_field('set.number').get_data(), {'number', ''})
        self.assertEqual(form.errors, {})


class FormReadonlyFieldsTest(unittest.TestCase):

    def test_readonly(self):
        'Accept of readonly fields'
        class _Form(Form):
            fields=[
                Field('first', convs.Int(), permissions='r'),
                Field('second', convs.Int()),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assert_(form.accept(dict(first='1', second='2')))
        self.assertEqual(form.python_data, {'first':None, 'second':2})

    def test_with_initial(self):
        'Accept of readonly fields with initial values'
        class _Form(Form):
            fields=[
                Field('first', convs.Int(), initial=1, permissions='r'),
                Field('second', convs.Int()),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assert_(form.accept(dict(first='3', second='2')))
        self.assertEqual(form.python_data, {'first':1, 'second':2})
        self.assertEqual(form.get_data(), {'first':'1', 'second':'2'})

    def test_fieldset(self):
        'Accept of readonly fieldset with initial values'
        class _Form(Form):
            fields=[
                FieldSet('set', fields=[
                    Field('first', convs.Int(), initial=1, permissions='r'),
                    Field('second', convs.Int(), initial=2),
                ]),
                Field('third', convs.Int()),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assert_(form.accept({'set':{'first': '2',
                                         'second': '2'},
                                  'third': '3'}))
        self.assertEqual(form.python_data, {'set': {'first': 1,
                                                    'second': 2},
                                            'third': 3})
        self.assertEqual(form.get_data(), {'set':{'first': '1',
                                                  'second': '2'},
                                           'third':'3'})

    def test_fieldlist(self):
        'Accept of readonly fieldlist with initial values'
        class _Form(Form):
            fields=[
                FieldList('list', field=Field('number', convs.Int(), permissions='r')),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'list':[5, 6]})
        self.assertEqual(form.python_data, {'list': [5, 6]})
        self.assert_(form.accept(dict(list=[{'1':1}, {'2':2}]) ) )
        self.assertEqual(form.python_data, {'list': [5, 6]})

    def test_fieldlist_of_fieldsets(self):
        'Accept of fieldlist of readonly fieldsets'
        class _Form(Form):
            fields=[
                FieldList('list', field=FieldSet(
                    'set',
                    fields=[Field('number', convs.Int(), permissions='r')],
                )),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'list':[{'number':1}, {'number':2}]})
        self.assertEqual(form.raw_data, MultiDict((('list-indices', '1'), ('list-indices', '2')), **{'list.1.number': '1', 'list.2.number': '2'}))
        self.assertEqual(form.python_data, {'list': [{'number':1}, {'number':2}]})
        self.assert_(form.accept(MultiDict((('list-indices', '1'),
                                            ('list-indices', '2')),
                                           **{'list.1.number': '2', 'list.2.number': '3'})))
        self.assertEqual(form.python_data, {'list': [{'number':1}, {'number':2}]})

    def test_fieldset_of_fieldsets(self):
        'Accept of readonly fieldset of fieldsets'
        class _Form(Form):
            fields=[
                FieldSet('sets', fields=[
                    FieldSet('set1', fields=[
                        Field('first', convs.Int(), permissions='r'),
                        Field('second', convs.Int()),
                    ]),
                    FieldSet('set2', fields=[
                        Field('first', convs.Int()),
                        Field('second', convs.Int(), permissions='r'),
                    ]),
                ]),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'sets':{
            'set1': {'first': 1, 'second': 2},
            'set2': {'first': 1, 'second': 2},
        }})

        self.assertEqual(form.get_data(),
            {'sets':{'set1':{'first': '1',
                             'second': '2',},
                     'set2':{'first': '1',
                             'second': '2'}},
        })

        self.assert_(form.accept(
            {'sets':{'set1':{'first': 'incorrect',
                             'second': '2',},
                     'set2':{'first': '1',
                             'second': 'incorrect'}},

            }
        ))

        self.assertEqual(form.python_data, {'sets': {
            'set1': {'first': 1, 'second': 2},
            'set2': {'first': 1, 'second': 2},
        }})

        self.assertEqual(form.get_data(),
            {'sets':{'set1':{'first': '1',
                             'second': '2',},
                     'set2':{'first': '1',
                             'second': '2'}},
        })

    def test_fieldset_of_fieldsets_with_noreq(self):
        'Accept of readonly fieldset of fieldsets with required=False'
        class _Form(Form):
            fields=[
                FieldSet('sets', fields=[
                    FieldSet('set1', fields=[
                        Field('first', convs.Int(required=False), permissions='r'),
                        Field('second', convs.Int()),
                    ]),
                    FieldSet('set2', fields=[
                        Field('first', convs.Int()),
                        Field('second', convs.Int(required=False), permissions='r'),
                    ]),
                ]),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'sets':{
            'set1': {'first': None, 'second': 2},
            'set2': {'first': 1, 'second': None},
        }})

        self.assertEqual(form.get_data(),
            {'sets':{'set1':{'first': '',
                             'second': '2',},
                     'set2':{'first': '1',
                            'second': ''}},
            })

        self.assert_(form.accept(
            {'sets':{'set1':{'first': 'incorrect',
                             'second': '2',},
                     'set2':{'first': '1',
                             'second': 'incorrect'}},

            }
        ))

        self.assertEqual(form.python_data, {'sets': {
            'set1': {'first': None, 'second': 2},
            'set2': {'first': 1, 'second': None},
        }})

        self.assertEqual(form.get_data(),
            {'sets':{'set1':{'first': '',
                             'second': '2',},
                     'set2':{'first': '1',
                            'second': ''}},
            })
