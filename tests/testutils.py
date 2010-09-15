# -*- coding: utf-8 -*-

import unittest
from insanities.forms import *


class MockEnvironment(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def gettext(self, template, count):
        return template


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


class FormTestCase(unittest.TestCase):

    def env(self, **kwargs):
        return MockEnvironment(**kwargs)
