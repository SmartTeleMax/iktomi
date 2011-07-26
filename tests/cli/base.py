# -*- coding: utf-8 -*-

import unittest
import datetime
from insanities.cli.base import Cli, manage, argument

__all__ = ['CliTest']


class CliTest(unittest.TestCase):

    def test_manage(self):
        '`cli` manage'
        assrt = self.assertEquals
        class TestCommand(Cli):
            def command_test(self, arg, kwarg=None, kwarg2=False):
                assrt(arg, 'arg1')
                assrt(kwarg, 'kwarg3')
                assrt(kwarg2, False)
        test_cmd = TestCommand()
        argv = 'mage.py test:test arg1 --kwarg=kwarg3'
        manage(dict(test=test_cmd), argv.split())

    def test_function_as_command(self):
        '`cli` function as a command'
        def cmd(arg, kwarg=None, kwarg2=False):
            self.assertEquals(arg, 'arg')
            self.assertEquals(kwarg, 'kwarg')
            self.assertEquals(kwarg2, True)
        argv = 'mage.py test arg --kwarg=kwarg --kwarg2'
        manage(dict(test=cmd), argv.split())

    def test_function_with_convs_as_command(self):
        '`cli` function with converters as a command'
        @argument(0, argument.to_int)
        @argument('kwarg', argument.to_date)
        def cmd(arg, kwarg=None, kwarg2=False):
            self.assertEquals(arg, 1)
            self.assertEquals(kwarg, datetime.date(2010, 6, 9))
            self.assertEquals(kwarg2, True)
        argv = 'mage.py test 1 --kwarg=9/6/2010 --kwarg2'
        manage(dict(test=cmd), argv.split())

    def test_convs(self):
        '`cli` converter'
        assrt = self.assertEquals
        class TestCommand(Cli):
            @argument(1, argument.to_int)
            @argument('kwarg', argument.to_date)
            def command_test(self, arg, kwarg=None, kwarg2=False):
                assrt(arg, 1)
                assrt(kwarg, datetime.date(2010, 6, 9))
                assrt(kwarg2, True)
        test_cmd = TestCommand()
        argv = 'mage.py test:test 1 --kwarg=9/6/2010 --kwarg2'
        manage(dict(test=test_cmd), argv.split())

    def test_convs_errors(self):
        '`cli` converter error'
        def init_cmd():
            class TestCommand(Cli):
                @argument(1, argument.to_int)
                @argument(u'kwarg', argument.to_date)
                def command_test(self, arg, kwarg=None, kwarg2=False):
                    pass
            return TestCommand
        self.assertRaises(AssertionError, init_cmd)

    def test_incorrect_call(self):
        '`cli` incorrect call'
        assrt = self.assertEquals
        class TestCommand(Cli):
            def command_test(self, arg, kwarg=None, kwarg2=False):
                pass
        argv = 'mage.py test'
        self.assertRaises(SystemExit, lambda: manage(dict(test=TestCommand()), argv.split()))
