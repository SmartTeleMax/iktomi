#!venv/bin/python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import unittest
from unittest import defaultTestLoader as dtl

from auth import *
from storage import *
from utils.storage import *
from utils.html import *
from utils.url import *
from utils.odict import *

from cli.base import *

from web.chain import *
from web.reverse import *
from web.convs import *
from web.filter import *

from forms.convs import *
from forms.fields import *
from forms.forms import *
from forms.media import *

suite = unittest.TestSuite()

for item in locals().values():
    if isinstance(item, type) and issubclass(item, unittest.TestCase):
        suite.addTest(dtl.loadTestsFromTestCase(item))

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
