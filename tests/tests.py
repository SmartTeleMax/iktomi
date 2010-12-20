#!venv/bin/python
# -*- coding: utf-8 -*-

import unittest
from unittest import defaultTestLoader as dtl

from utils.storage import *
from utils.html import *
from utils.url import *

from web.chain import *
from web.convs import *
from web.filter import *

from forms.convs import *
from forms.fields import *
from forms.forms import *

suite = unittest.TestSuite()

for item in locals().values():
    if isinstance(item, type) and issubclass(item, unittest.TestCase):
        suite.addTest(dtl.loadTestsFromTestCase(item))

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
