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

