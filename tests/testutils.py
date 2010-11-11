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


class MockField(object):
    def __init__(self,conv, env):
        self.conv = conv(field=self)
        self.env = env
    def get_default(self):
        return ''


class FormTestCase(unittest.TestCase):

    def env(self, **kwargs):
        return kwargs
