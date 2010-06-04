# -*- coding: utf-8 -*-

import unittest
import sys
import os
FRAMEWORK_DIR = os.path.abspath('../..')
sys.path.append(FRAMEWORK_DIR)
from insanities.web.core import Map, RequestHandler
from insanities.web.filters import *
from insanities.web.http import Request, RequestContext
from insanities.web.urlconvs import *


class IntConverter(unittest.TestCase):

    def test_to_python(self):
        conv = Integer()
        value = conv.to_python(u'4')
        self.assertEqual(value, 4)

    def test_to_python_fail(self):
        conv = Integer()
        self.assertRaises(ConvertError, lambda : conv.to_python(u'4w'))

    def test_to_url(self):
        conv = Integer()
        value = conv.to_url(4)
        self.assertEqual(value, '4')


class StringConverter(unittest.TestCase):

    def test_to_python(self):
        conv = String()
        value = conv.to_python('%60%25%27')
        #XXX: new converters interface
        #self.assertEqual(value, '`%\'')

    def test_to_url(self):
        conv = String()
        value = conv.to_url('`%\'')
        #self.assertEqual(value, '%60%25%27')
