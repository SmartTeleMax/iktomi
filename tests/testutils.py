# -*- coding: utf-8 -*-

import unittest
from insanities.forms import *


class MockEnvironment(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def gettext(self, template, count):
        return template
    def render(self, template_name, **kwargs):
        return template_name, kwargs


class FormTestCase(unittest.TestCase):

    def env(self, **kwargs):
        return MockEnvironment(**kwargs)

    def instantiate_conv(self, conv, value=None):
        class SampleForm(Form):
            fields=[Field(name='input', conv=conv)]
        return SampleForm(self.env(), initial={'input': value}).get_field('input').conv
