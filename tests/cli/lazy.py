# coding: utf-8

import os
import unittest
from iktomi.cli.lazy import LazyCli
from iktomi.cli.base import Cli

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
