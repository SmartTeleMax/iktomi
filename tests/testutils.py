# -*- coding: utf-8 -*-

import unittest
from insanities.forms import *


class MockForm(object):
    permissions = set('rw')
    name = ''
    prefix = ''
    def __init__(self, *fields, **kw):
        self.fields = [f(parent=self) for f in fields]
        self.__dict__.update(kw)
    @property
    def form(self):
        return self


def MockField(conv, env):
    class _Form(Form):
        fields=[Field('field', conv)]
    return _Form(env=env).fields[0]


class FormTestCase(unittest.TestCase):

    def env(self, **kwargs):
        return kwargs
