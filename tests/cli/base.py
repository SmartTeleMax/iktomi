# -*- coding: utf-8 -*-
import os
import sys
import unittest
import datetime
from iktomi.cli.base import Cli, manage, argument
from cStringIO import StringIO

__all__ = ['CliTest']

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


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

    def test_digest_not_found(self):
        class TestCommand(Cli):
            def command_test(self, kwarg=None, kwarg2=False):
                pass
        argv = 'mage.py test1:test --kwarg --kwarg2'

        out = StringIO()
        with patch.object(sys, 'stdout', out):
            with self.assertRaises(SystemExit):
                manage(dict(test=TestCommand()), argv.split())
            self.assertEqual('Commands:\ntest\n', out.getvalue())

    def test_no_command_provided(self):
        class TestCommand(Cli):
            def command_test(self, kwarg=None, kwarg2=False):
                pass
        argv = 'mage.py'

        out = StringIO()
        with patch.object(sys, 'stdout', out):
            with self.assertRaises(SystemExit):
                manage(dict(test=TestCommand()), argv.split())
            self.assertEqual('Commands:\ntest\n', out.getvalue())

    def test_test_command_not_found(self):
        class TestCommand(Cli):
            def command_test(self, kwarg=None, kwarg2=False):
                pass
        argv = 'mage.py test:test1 --kwarg --kwarg2'

        out = StringIO()
        with patch.object(sys, 'stdout', out):
            with self.assertRaises(SystemExit):
                manage(dict(test=TestCommand()), argv.split())
            self.assertEqual('test\ntest\n\t./mage.py test:test [kwarg] [kwarg2]\n',
                             out.getvalue())

    def test_documented_function_description(self):
        class TestCommand(Cli):
            def command_test(self, kwarg=None, kwarg2=False):
                "Documentation goes here"
                pass

        cli_command = TestCommand()
        out = StringIO()
        with patch.object(sys, 'stdout', out):
            cli_command('help')
            expected_help = "testcommand\ntestcommand\n\t./manage.py "+\
                            "testcommand:test [kwarg] [kwarg2]\n\t\t"+\
                            "Documentation goes here\n"
            self.assertEqual(expected_help, out.getvalue())

    def test_converter_int_error(self):
        class TestCommand(Cli):
            @argument('kwarg', argument.to_int)
            def command_test(self, kwarg):
                pass
        test_cmd = TestCommand()
        argv = 'mage.py test:test --kwarg=noint'
        err = StringIO()
        with patch.object(sys, 'stderr', err):
            manage(dict(test=test_cmd), argv.split())
            self.assertEqual('One of the arguments for command "test" is wrong:\n'+\
                             'Cannot convert \'noint\' to int', err.getvalue())

    def test_converter_date_error(self):
        class TestCommand(Cli):
            @argument('kwarg', argument.to_date)
            def command_test(self, kwarg):
                pass
        test_cmd = TestCommand()
        argv = 'mage.py test:test --kwarg=nodate'
        err = StringIO()
        with patch.object(sys, 'stderr', err):
            manage(dict(test=test_cmd), argv.split())
            self.assertEqual('One of the arguments for command "test" is wrong:\n'+\
                             'Cannot convert \'nodate\' to date, please provide '+\
                             'string in format "dd/mm/yyyy"', err.getvalue())

    def test_argument_call_error(self):
        class TestCommand(Cli):
            @argument(2, argument.to_int)
            def command_test(self, arg, kwarg=None):
                pass
        argv = 'mage.py test:test --kwarg=test 1'
        test_cmd = TestCommand()
        manage(dict(test=test_cmd), argv.split())
        err = StringIO()
        with patch.object(sys, 'stderr', err):
            manage(dict(test=test_cmd), argv.split())
            self.assertEqual('One of the arguments for command "test" is wrong:\n'+\
                             'Total positional args = 2, but you apply converter '+\
                             'for 2 argument (indexing starts from 0)', err.getvalue())

    def test_argument_required(self):
        class TestCommand(Cli):
            @argument('kwarg', argument.to_int, required=True)
            def command_test(self, kwarg=1, kwarg2=None):
                pass
        argv = 'mage.py test:test --kwarg2=1'
        test_cmd = TestCommand()
        manage(dict(test=test_cmd), argv.split())
        err = StringIO()
        with patch.object(sys, 'stderr', err):
            manage(dict(test=test_cmd), argv.split())
            self.assertEqual('One of the arguments for command "test" is wrong:\n'+\
                             'Keyword argument "kwarg" is required', err.getvalue())

    def test_autocomplete(self):
        class TestCommand(Cli):
            def command_process(self, kwarg):
                pass

        argv = 'mage.py'
        test_cmd = TestCommand()
        with patch.dict('os.environ', {'IKTOMI_AUTO_COMPLETE':'1',
                                       'COMP_WORDS':argv,
                                       'COMP_CWORD':'1' }):
            out = StringIO()
            with patch.object(sys, 'stdout', out):
                with self.assertRaises(SystemExit):
                    manage(dict(test=test_cmd), argv.split())
            self.assertEqual('test test:', out.getvalue())

        argv = 'mage.py te'
        test_cmd = TestCommand()
        with patch.dict('os.environ', {'IKTOMI_AUTO_COMPLETE':'1',
                                       'COMP_WORDS':argv,
                                       'COMP_CWORD':'1' }):
            out = StringIO()
            with patch.object(sys, 'stdout', out):
                with self.assertRaises(SystemExit):
                    manage(dict(test=test_cmd), argv.split())
            self.assertEqual('test test:', out.getvalue())

        argv = 'mage.py test:'
        test_cmd = TestCommand()
        with patch.dict('os.environ', {'IKTOMI_AUTO_COMPLETE':'1',
                                       'COMP_WORDS':argv.replace(":", " : "),
                                       'COMP_CWORD':'2' }):
            out = StringIO()
            with patch.object(sys, 'stdout', out):
                with self.assertRaises(SystemExit):
                    manage(dict(test=test_cmd), argv.split())
            self.assertEqual('process', out.getvalue())
        argv = 'mage.py test:pr'
        test_cmd = TestCommand()

        with patch.dict('os.environ', {'IKTOMI_AUTO_COMPLETE':'1',
                                       'COMP_WORDS':argv.replace(":", " : "),
                                       'COMP_CWORD':'3' }):
            out = StringIO()
            with patch.object(sys, 'stdout', out):
                with self.assertRaises(SystemExit):
                    manage(dict(test=test_cmd), argv.split())
            self.assertEqual('process', out.getvalue())
