#!venv/bin/python
# -*- coding: utf-8 -*-

import unittest
from unittest import defaultTestLoader as dtl
from inspect import isclass


# JINJA2 staff
from jinja2 import Environment, PackageLoader
from insanities.ext.jinja2 import FormEnvironment
jinja_env = Environment(loader=PackageLoader('insanities', 'templates'))
env = FormEnvironment(jinja_env)

from utils import *
from web import *
from forms import *
from ext import *

suite = unittest.TestSuite()

# Adding tests in one suite
for item in locals().values():
    if isclass(item) and issubclass(item, unittest.TestCase):
        suite.addTest(dtl.loadTestsFromTestCase(item))

if __name__ == '__main__':
    # Running tests in textmode
    unittest.TextTestRunner(verbosity=2).run(suite)
