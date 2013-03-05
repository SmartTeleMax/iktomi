# coding: utf-8

import os
import unittest
from iktomi.cli.fcgi import Flup


class FlupTests(unittest.TestCase):

    def test_default_init(self):
        flup = Flup("app")
        cwd = os.path.abspath('.')
        self.assertEqual(flup.app, "app")
        self.assertEqual(flup.cwd, cwd)
        self.assertEqual(flup.bind, os.path.join(cwd, 'fcgi.sock'))
        self.assertEqual(flup.logfile, os.path.join(cwd, 'fcgi.log'))
        self.assertEqual(flup.pidfile, os.path.join(cwd, 'fcgi.pid'))
