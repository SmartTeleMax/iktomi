# -*- coding: utf-8 -*-

import unittest

from iktomi.forms import *
from webob.multidict import MultiDict
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
        self.assertEqual(form.raw_data, {'first':'', 'second':''})
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
        self.assertEqual(form.raw_data, {'first':'1', 'second':'2'})
        self.assertEqual(form.python_data, {'first':1, 'second':2})

    def test_with_initial(self):
        'Initialization of form object with initial values'
        class F(Form):
            fields=[
                Field('first', convs.Int()),
                Field('second', convs.Int()),
            ]
        env = AppEnvironment.create()
        form = F(env, initial={'first':1, 'second':2})
        self.assertEqual(form.initial, {'first':1, 'second':2})
        self.assertEqual(form.raw_data, {'first':'1', 'second':'2'})
        self.assertEqual(form.python_data, {'first':1, 'second':2})

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
        self.assertEqual(form.raw_data, {'first':'1', 'second':'2'})
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
        self.assertEqual(form.raw_data, {'set.first': '1', 'set.second': '2'})
        self.assertEqual(form.python_data, {'set': {'first': 1, 'second': 2}})

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
        self.assertEqual(form.raw_data, {'set.first': '', 'set.second': '2'})
        self.assertEqual(form.python_data, {'set': {'first': None, 'second': 2}})

    def test_init_fieldlist_with_initial(self):
        'Initialization of form object with fieldlist with initial values'
        class _Form(Form):
            fields=[
                FieldList('list', field=Field('number', convs.Int())),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'list': [1, 2]})
        self.assertEqual(form.raw_data, MultiDict([('list-indices', '1'), 
                                                   ('list-indices', '2'),
                                                   ('list.1', '1'),
                                                   ('list.2', '2')
                                                  ]))
        self.assertEqual(form.python_data, {'list': [1, 2]})

    def test_fieldlist_with_initial_and_initial(self):
        'Initialization of form object with fieldlist with initial and initial values'
        class _Form(Form):
            fields=[
                FieldList('list', field=Field('number', convs.Int(), initial=2)),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'list': [1, 2]})
        self.assertEqual(form.raw_data, MultiDict([('list-indices', '1'),
                                                   ('list-indices', '2'),
                                                   ('list.1', '1'),
                                                   ('list.2', '2')
                                                  ]))
        self.assertEqual(form.python_data, {'list': [1, 2]})


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
        self.assert_(not form.accept(MultiDict(first='1')))
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
        self.assert_(not form.accept(MultiDict(**{'set.first': '2d', 'set.second': '', 'third': '3f'})))
        self.assertEqual(form.python_data, {'set': {'first': 1, 'second': 2}, 'third': None})
        self.assertEqual(form.errors, {'set.second': convs.Int.error_required, 
                                       'third': convs.Int.error_notvalid})
        self.assertEqual(form.raw_data, MultiDict(**{'set.first': '1', 'set.second': '', 'third': '3f'}))

    def test_fieldlist_with_initial_delete(self):
        'Fieldlist element deletion'
        class _Form(Form):
            fields=[
                FieldList('list', field=Field('number', convs.Int())),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'list': [1, 2, 3]})
        self.assertEqual(form.raw_data, MultiDict((('list-indices', '1'), ('list-indices', '2'), ('list-indices', '3')), 
                                                  **{'list.1': '1', 'list.2': '2', 'list.3': '3'}))
        self.assertEqual(form.python_data, {'list': [1, 2, 3]})
        self.assert_(form.accept(MultiDict((('list-indices', '1'), ('list-indices', '3')), 
                                                  **{'list.1': '1', 'list.3': '3'})))
        self.assertEqual(form.python_data, {'list': [1, 3]})

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
        self.assert_(form.accept(MultiDict(first='1', second='2')))
        self.assertEqual(form.initial, {})
        self.assertEqual(form.raw_data, {'first':'1', 'second':'2'})
        self.assertEqual(form.python_data, {'first':1, 'second':2})

    def test_with_initial(self):
        'Accept with initial values'
        class _Form(Form):
            fields=[
                Field('first', convs.Int(), initial=2),
                Field('second', convs.Int(required=False), get_initial=lambda: 2),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        form.accept(MultiDict(first='1'))
        self.assert_(form.accept(MultiDict(first='1')))
        self.assertEqual(form.initial, {})
        self.assertEqual(form.python_data, {'first':1, 'second':None})

    def test_with_initial(self):
        'Accept with initial data'
        class _Form(Form):
            fields=[
                Field('first', convs.Int()),
                Field('second', convs.Int()),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'second':3})
        self.assert_(form.accept(MultiDict(first='1', second='2')))
        self.assertEqual(form.initial, {'second': 3})
        self.assertEqual(form.python_data, {'first':1, 'second':2})

    def test_fieldlist_is_required(self):
        'Fieldlist is required and accepted value is empty'
        class _Form(Form):
            fields=[
                FieldList('list', field=Field('number', convs.Int())),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assertEqual(form.raw_data, MultiDict())
        self.assertEqual(form.python_data, {'list': []})
        self.assert_(form.accept(MultiDict()))
        self.assertEqual(form.python_data, {'list': []})
        self.assertEqual(form.errors, {})

    def test_fieldset_is_required(self):
        'Fieldset is required and accepted value is empty'
        class _Form(Form):
            fields=[
                FieldSet('set', fields=[Field('number', convs.Int())]),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assertEqual(form.raw_data, MultiDict([('set.number', '')]))
        self.assertEqual(form.python_data, {'set': {'number': None}})
        self.assert_(form.accept({}))
        self.assertEqual(form.python_data, {'set': {'number': None}})
        self.assertEqual(form.get_field('set.number').raw_value, '')
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
        self.assert_(form.accept(MultiDict(first='1', second='2')))
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
        self.assert_(form.accept(MultiDict(first='3', second='2')))
        self.assertEqual(form.python_data, {'first':1, 'second':2})
        self.assertEqual(form.raw_data, {'first':'1', 'second':'2'})

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
        self.assert_(form.accept(MultiDict(**{'set.first': '2', 'set.second': '2', 'third': '3'})))
        self.assertEqual(form.python_data, {'set': {'first': 1, 'second': 2}, 'third': 3})
        self.assertEqual(form.raw_data, MultiDict(**{'set.first': '1', 'set.second': '2', 'third':'3'}))

    def test_fieldlist(self):
        'Accept of readonly fieldlist with initial values'
        class _Form(Form):
            fields=[
                FieldList('list', field=Field('number', convs.Int(), permissions='r')),
            ]
        env = AppEnvironment.create()
        form = _Form(env, initial={'list':[1, 2]})
        self.assertEqual(sorted(form.raw_data.items()),
            [('list-indices', '1'),
             ('list-indices', '2'),
             ('list.1', '1'), 
             ('list.2', '2')])
        self.assertEqual(form.python_data, {'list': [1, 2]})
        self.assert_(form.accept(MultiDict((('list-indices', '1'),
                                            ('list-indices', 'aa'),
                                            ('list-indices', '2')),
                                            **{'list.1': '2',
                                               'list.2': '3'})))
        self.assertEqual(form.python_data, {'list': [1, 2]})

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

        self.assertEqual(dict(form.raw_data), MultiDict(**{
            'sets.set1.first': '1',
            'sets.set1.second': '2',
            'sets.set2.first': '1',
            'sets.set2.second': '2',
        }))

        self.assert_(form.accept(MultiDict(**{
            'sets.set1.first': 'incorect',
            'sets.set1.second': '2',
            'sets.set2.first': '1',
            'sets.set2.second': 'incorect',
        })))

        self.assertEqual(form.python_data, {'sets': {
            'set1': {'first': 1, 'second': 2}, 
            'set2': {'first': 1, 'second': 2}, 
        }})

        self.assertEqual(form.raw_data, MultiDict(**{
            'sets.set1.first': '1',
            'sets.set1.second': '2',
            'sets.set2.first': '1',
            'sets.set2.second': '2',
        }))

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

        self.assertEqual(form.raw_data, MultiDict(**{
            'sets.set1.first': '',
            'sets.set1.second': '2',
            'sets.set2.first': '1',
            'sets.set2.second': '',
        }))

        self.assert_(form.accept(MultiDict(**{
            'sets.set1.first': 'incorect',
            'sets.set1.second': '2',
            'sets.set2.first': '1',
            'sets.set2.second': 'incorect',
        })))

        self.assertEqual(form.python_data, {'sets': {
            'set1': {'first': None, 'second': 2}, 
            'set2': {'first': 1, 'second': None}, 
        }})

        self.assertEqual(form.raw_data, MultiDict(**{
            'sets.set1.first': '',
            'sets.set1.second': '2',
            'sets.set2.first': '1',
            'sets.set2.second': '',
        }))


class FormFieldListErrorsTests(unittest.TestCase):

    def test_fieldlist(self):
        'Fieldlist errors'
        class _Form(Form):
            fields=[
                FieldList('list', field=Field('number', convs.Int())),
            ]
        env = AppEnvironment.create()
        form = _Form(env)
        self.assertEqual(form.raw_data, MultiDict())
        self.assertEqual(form.python_data, {'list': []})
        self.assert_(not form.accept(MultiDict((('list-indices', '1'), ('list-indices', '2'), ('list-indices', '3')), 
                                           **{'list.1': '1', 'list.2': '2', 'list.3': '3s'})))
        self.assertEqual(form.python_data, {'list': [1, 2, None]})
        self.assertEqual(form.errors, {'list.3': convs.Int.error_notvalid})

    def test_fieldlist_with_initial(self):
        '''Fieldlist errors (list of one initial value), when submiting
        new value before initial and incorrect value insted of initial'''
        class F(Form):
            fields=[
                FieldList('list', field=Field('number', convs.Int())),
            ]
        env = AppEnvironment.create()
        form = F(env, initial={'list': [1]})
        self.assertEqual(form.raw_data, MultiDict((('list-indices', '1'),), 
                                           **{'list.1': '1'}))
        self.assertEqual(form.python_data, {'list': [1]})
        self.assert_(not form.accept(MultiDict((('list-indices', '2'), ('list-indices', '1')), 
                                           **{'list.1': '1s', 'list.2': '2'})))
        self.assertEqual(form.python_data, {'list': [2, 1]})
        self.assertEqual(form.errors, {'list.1': convs.Int.error_notvalid})
