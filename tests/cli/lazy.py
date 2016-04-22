# coding: utf-8

import os
import sys
import unittest
from iktomi.cli.lazy import LazyCli
from iktomi.cli.base import Cli, manage
from cStringIO import StringIO

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


class MyCli(Cli):

    'Example Cli class'

    called = False

    def command_run(self, arg):
        self.called = arg


class LazyTests(unittest.TestCase):

    def test_lazy_call(self):
        @LazyCli
        def cli():
            return MyCli()

        self.assertIsInstance(cli.digest, MyCli)

        print cli.description()
        self.assertEqual(cli.description().splitlines()[0],
                         'mycli')
        self.assertEqual(cli.description().splitlines()[1],
                         'Example Cli class')
        cli('run', True)
        self.assertTrue(cli.digest.called)

    def test_lazyness(self):
        @LazyCli
        def cli():
            # This should be called only on cli.digest property call.
            # Not earlier.
            raise ValueError

        self.assertRaises(ValueError, lambda: cli.digest)

    def test_lazy_autocomplete(self):
        @LazyCli
        def cli():
            return MyCli()

        argv = 'manage.py fruit:'
        with patch.dict('os.environ', {'IKTOMI_AUTO_COMPLETE':'1',
                                       'COMP_WORDS':argv.replace(":", " : "),
                                       'COMP_CWORD':'2' }):
            out = StringIO()
            with patch.object(sys, 'stdout', out):
                with self.assertRaises(SystemExit):
                    manage(dict(fruit=cli), argv.split())
            self.assertEqual('run', out.getvalue())
