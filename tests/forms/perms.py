# -*- coding: utf-8 -*-

import unittest

from iktomi.forms import *
from iktomi.web.app import AppEnvironment


class PermissionsTests(unittest.TestCase):

    def test_init(self):
        'Initialization of form object'
        class F(Form):
            fields=[
                Field('first', permissions='rw'),
                Field('second'),
            ]
        env = AppEnvironment.create()
        form = F(env, permissions='rwx')
        self.assertEqual(form.permissions, set('rwx'))
        self.assertEqual(form.get_field('second').permissions, set('rwx'))
        self.assertEqual(form.get_field('first').permissions, set('rw'))

        form = F(env, permissions='r')
        self.assertEqual(form.permissions, set('r'))
        self.assertEqual(form.get_field('second').permissions, set('r'))
        self.assertEqual(form.get_field('first').permissions, set('r'))

    def test_get_perms(self):
        class F(Form):
            fields=[
                Field('first', permissions='rw'),
                Field('second'),
            ]
        env = AppEnvironment.create()
        form = F(env, permissions='rwx')
        first = form.get_field('first')
        second = form.get_field('second')
        self.assertEqual(first.perm_getter.get_perms(first), set(['r', 'w']))
        self.assertEqual(second.perm_getter.get_perms(second), set(['r', 'w', 'x']))

    def test_perm_getter_repr(self):
        class F(Form):
            fields=[
                Field('first', permissions='rw'),
                Field('second'),
            ]
        env = AppEnvironment.create()
        form = F(env, permissions='rwx')
        field = form.get_field('first')
        self.assertEqual(repr(field.perm_getter), "FieldPerm(set(['r', 'w']))")
