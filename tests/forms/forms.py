# -*- coding: utf-8 -*-

import unittest

from insanities.forms import *
from webob.multidict import MultiDict


class FormClassInitializationTests(unittest.TestCase):

    def test_init(self):
        'Initialization of form object'
        class _Form(Form):
            fields=[
                Field('first', convs.Int()),
                Field('second', convs.Int()),
            ]
        form = _Form()
        self.assertEqual(form.initial, {})
        self.assertEqual(form.raw_data, {'first':'', 'second':''})
        self.assertEqual(form.python_data, {'first':None, 'second':None})

    def test_with_default(self):
        'Initialization of form object with fields default values'
        class _Form(Form):
            fields=[
                Field('first', convs.Int(), default=1),
                Field('second', convs.Int(), get_default=lambda: 2),
            ]
        form = _Form()
        self.assertEqual(form.initial, {})
        self.assertEqual(form.raw_data, {'first':'1', 'second':'2'})
        self.assertEqual(form.python_data, {'first':1, 'second':2})

    def test_with_initial(self):
        'Initialization of form object with initial values'
        class _Form(Form):
            fields=[
                Field('first', convs.Int()),
                Field('second', convs.Int()),
            ]
        form = _Form(initial={'first':1, 'second':2})
        self.assertEqual(form.initial, {'first':1, 'second':2})
        self.assertEqual(form.raw_data, {'first':'1', 'second':'2'})
        self.assertEqual(form.python_data, {'first':1, 'second':2})

    def test_with_initial_and_default(self):
        'Initialization of form object with initial and default values'
        class _Form(Form):
            fields=[
                Field('first', convs.Int(), default=3),
                Field('second', convs.Int()),
            ]
        form = _Form(initial={'first':1, 'second':2})
        self.assertEqual(form.initial, {'first':1, 'second':2})
        self.assertEqual(form.raw_data, {'first':'1', 'second':'2'})
        self.assertEqual(form.python_data, {'first':1, 'second':2})


class FormClassAcceptTests(unittest.TestCase):
    def test_accept(self):
        'Initialization of form object'
        class _Form(Form):
            fields=[
                Field('first', convs.Int()),
                Field('second', convs.Int()),
            ]
        form = _Form()
        self.assert_(form.accept(MultiDict(first='1', second='2')))
        self.assertEqual(form.initial, {})
        self.assertEqual(form.raw_data, {'first':'1', 'second':'2'})
        self.assertEqual(form.python_data, {'first':1, 'second':2})

    def test_with_default(self):
        'Initialization of form object'
        class _Form(Form):
            fields=[
                Field('first', convs.Int(), default=2),
                Field('second', convs.Int(required=False), get_default=lambda: 2),
            ]
        form = _Form()
        self.assert_(form.accept(MultiDict(first='1')))
        self.assertEqual(form.initial, {})
        self.assertEqual(form.python_data, {'first':1, 'second':None})

    def test_with_initial(self):
        'Initialization of form object'
        class _Form(Form):
            fields=[
                Field('first', convs.Int()),
                Field('second', convs.Int()),
            ]
        form = _Form(initial={'second':3})
        self.assert_(form.accept(MultiDict(first='1', second='2')))
        self.assertEqual(form.initial, {'second':3})
        self.assertEqual(form.python_data, {'first':1, 'second':2})
