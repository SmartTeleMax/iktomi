# -*- coding: utf-8 -*-
import sys
import unittest
import datetime
from iktomi.cli.base import Cli, manage, argument
import six

from io import BytesIO

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
            def command_avocado(self, arg, kwarg=None, kwarg2=False):
                assrt(arg, 'arg1')
                assrt(kwarg, 'kwarg3')
                assrt(kwarg2, False)
                sys.stdout.write(b"Completed\n")

        test_cmd = TestCommand()
        argv = 'manage.py fruit:avocado arg1 --kwarg=kwarg3'
        out = BytesIO()
        with patch.object(sys, 'stdout', out):
            manage(dict(fruit=test_cmd), argv.split())
        self.assertEqual(b"Completed\n", out.getvalue())

    def test_function_as_command(self):
        '`cli` function as a command'
        def cmd(arg, kwarg=None, kwarg2=False, kwarg3=False):
            self.assertEquals(arg, 'arg')
            self.assertEquals(kwarg, 'kwarg')
            self.assertEquals(kwarg2, True)
            self.assertEquals(kwarg3, '')
            sys.stdout.write(b"Completed\n")

        argv = 'manage.py fruit arg --kwarg=kwarg --kwarg2 --kwarg3='
        out = BytesIO()
        with patch.object(sys, 'stdout', out):
            manage(dict(fruit=cmd), argv.split())
        self.assertEqual(b"Completed\n", out.getvalue())

    def test_function_with_convs_as_command(self):
        '`cli` function with converters as a command'
        @argument(0, argument.to_int)
        @argument('kwarg', argument.to_date)
        def cmd(arg, kwarg=None, kwarg2=False):
            self.assertEquals(arg, 1)
            self.assertEquals(kwarg, datetime.date(2010, 6, 9))
            self.assertEquals(kwarg2, True)
            sys.stdout.write(b"Completed\n")
        argv = 'manage.py fruit 1 --kwarg=9/6/2010 --kwarg2'
        out = BytesIO()
        with patch.object(sys, 'stdout', out):
            manage(dict(fruit=cmd), argv.split())
        self.assertEqual(b"Completed\n", out.getvalue())

    def test_convs(self):
        '`cli` converter'
        assrt = self.assertEquals
        class TestCommand(Cli):
            @argument(1, argument.to_int)
            @argument('kwarg', argument.to_date)
            def command_avocado(self, arg, kwarg=None, kwarg2=False):
                assrt(arg, 1)
                assrt(kwarg, datetime.date(2010, 6, 9))
                assrt(kwarg2, True)
                sys.stdout.write(b"Completed\n")

        test_cmd = TestCommand()
        argv = 'manage.py fruit:avocado 1 --kwarg=9/6/2010 --kwarg2'
        out = BytesIO()
        with patch.object(sys, 'stdout', out):
            manage(dict(fruit=test_cmd), argv.split())
        self.assertEqual(b"Completed\n", out.getvalue())

    def test_convs_errors(self):
        '`cli` converter error'
        with self.assertRaises(AssertionError):
            class TestCommand(Cli):
                @argument(1, argument.to_int)
                @argument(u'kwarg', argument.to_date)
                def command_avocado(self, arg, kwarg=None, kwarg2=False):
                    pass
            return TestCommand

    if six.PY3:
        test_convs_errors = unittest.expectedFailure(test_convs_errors)

    def test_incorrect_call(self):
        '`cli` incorrect call'
        class TestCommand(Cli):
            def command_avocado(self, arg, kwarg=None, kwarg2=False):
                pass
        argv = 'manage.py fruit'
        out = BytesIO()
        with patch.object(sys, 'stdout', out):
            with self.assertRaises(SystemExit) as exc:
                manage(dict(fruit=TestCommand()), argv.split())
            self.assertEqual(exc.exception.code,
                             'ERROR: "fruit" command digest requires command name')
        self.assertIn(b"fruit:avocado", out.getvalue())
        self.assertIn(b"manage.py", out.getvalue())
        self.assertNotIn(b"./manage.py", out.getvalue())

    def test_digest_not_found(self):
        class TestCommand(Cli):
            def command_avocado(self, kwarg=None, kwarg2=False):
                pass
        argv = 'manage.py vegetable:avocado --kwarg --kwarg2'

        out = BytesIO()
        with patch.object(sys, 'stdout', out):
            with self.assertRaises(SystemExit):
                manage(dict(fruit=TestCommand()), argv.split())
            self.assertEqual(b'Commands:\nfruit\n', out.getvalue())

    def test_no_command_provided(self):
        class TestCommand(Cli):
            def command_avocado(self, kwarg=None, kwarg2=False):
                pass
        argv = 'manage.py'

        out = BytesIO()
        with patch.object(sys, 'stdout', out):
            with self.assertRaises(SystemExit) as exc:
                manage(dict(fruit=TestCommand()), argv.split())
            self.assertEqual(b'Commands:\nfruit\n', out.getvalue())

    def test_command_not_found(self):
        class TestCommand(Cli):
            def command_avocado(self, kwarg=None, kwarg2=False):
                pass
        argv = 'manage.py fruit:orange --kwarg --kwarg2'

        out = BytesIO()
        with patch.object(sys, 'stdout', out):
            with self.assertRaises(SystemExit) as exc:
                manage(dict(fruit=TestCommand()), argv.split())
            self.assertEqual(exc.exception.code,
                             'ERROR: Command "fruit:orange" not found')
        self.assertIn(b'manage.py', out.getvalue())
        self.assertIn(b'fruit:avocado [kwarg] [kwarg2]', out.getvalue())

    def test_documented_function_description(self):
        class TestCommand(Cli):
            def command_avocado(self, kwarg=None, kwarg2=False):
                "Documentation goes here"
                pass

        cli_command = TestCommand()
        out = BytesIO()
        with patch.object(sys, 'stdout', out):
            cli_command('help')
            self.assertIn(b"manage.py", out.getvalue())
            self.assertNotIn(b"./manage.py", out.getvalue())
            self.assertIn(b"testcommand:avocado [kwarg] [kwarg2]", out.getvalue())
            self.assertIn(b"Documentation goes here", out.getvalue())

    def test_converter_int_error(self):
        class TestCommand(Cli):
            @argument('kwarg', argument.to_int)
            def command_avocado(self, kwarg):
                pass
        test_cmd = TestCommand()
        argv = 'manage.py fruit:avocado --kwarg=noint'
        err = BytesIO()
        with patch.object(sys, 'stderr', err):
            with self.assertRaises(SystemExit) as exc:
                manage(dict(fruit=test_cmd), argv.split())
            self.assertIn(b'One of the arguments for command "avocado" is wrong:',
                           err.getvalue())
            self.assertEqual('Cannot convert \'noint\' to int',
                             exc.exception.code.args[0])

    def test_converter_date_error(self):
        class TestCommand(Cli):
            @argument('kwarg', argument.to_date)
            def command_avocado(self, kwarg):
                pass
        test_cmd = TestCommand()
        argv = 'manage.py fruit:avocado --kwarg=nodate'
        err = BytesIO()
        with patch.object(sys, 'stderr', err):
            with self.assertRaises(SystemExit) as exc:
                manage(dict(fruit=test_cmd), argv.split())

            self.assertIn(b'One of the arguments for command "avocado" is wrong:',
                           err.getvalue())
            self.assertIn('Cannot convert \'nodate\' to date',
                          exc.exception.code.args[0])
            self.assertIn('dd/mm/yyyy',
                          exc.exception.code.args[0])

    def test_argument_call_error(self):
        class TestCommand(Cli):
            @argument(2, argument.to_int)
            def command_avocado(self, arg, kwarg=None):
                pass
        argv = 'manage.py fruit:avocado --kwarg=test 1'
        test_cmd = TestCommand()

        err = BytesIO()
        with patch.object(sys, 'stderr', err):
            with self.assertRaises(SystemExit) as exc:
                manage(dict(fruit=test_cmd), argv.split())
            self.assertIn(b'One of the arguments for command "avocado" is wrong:',
                           err.getvalue())
            self.assertEqual('Total positional args = 2, but you apply converter '+\
                             'for 2 argument (indexing starts from 0)',
                             exc.exception.code.args[0])

    def test_argument_required(self):
        class TestCommand(Cli):
            @argument('kwarg', argument.to_int, required=True)
            def command_avocado(self, kwarg=1, kwarg2=None):
                pass
        argv = 'manage.py fruit:avocado --kwarg2=1'
        test_cmd = TestCommand()

        err = BytesIO()
        with patch.object(sys, 'stderr', err):
            with self.assertRaises(SystemExit) as exc:
                manage(dict(fruit=test_cmd), argv.split())
            self.assertIn(b'One of the arguments for command "avocado" is wrong:',
                          err.getvalue())
            self.assertIn('Keyword argument "kwarg" is required',
                          exc.exception.code.args[0])

    def test_autocomplete(self):
        class TestCommand(Cli):
            def command_avocado(self, kwarg):
                pass

        argv = 'manage.py'
        test_cmd = TestCommand()
        with patch.dict('os.environ', {'IKTOMI_AUTO_COMPLETE':'1',
                                       'COMP_WORDS':argv,
                                       'COMP_CWORD':'1' }):
            out = BytesIO()
            with patch.object(sys, 'stdout', out):
                with self.assertRaises(SystemExit):
                    manage(dict(fruit=test_cmd), argv.split())
            self.assertEqual(b'fruit fruit:', out.getvalue())

        argv = 'manage.py fr'
        test_cmd = TestCommand()
        with patch.dict('os.environ', {'IKTOMI_AUTO_COMPLETE':'1',
                                       'COMP_WORDS':argv,
                                       'COMP_CWORD':'1' }):
            out = BytesIO()
            with patch.object(sys, 'stdout', out):
                with self.assertRaises(SystemExit):
                    manage(dict(fruit=test_cmd), argv.split())
            self.assertEqual(b'fruit fruit:', out.getvalue())

        argv = 'manage.py fruit:'
        test_cmd = TestCommand()
        with patch.dict('os.environ', {'IKTOMI_AUTO_COMPLETE':'1',
                                       'COMP_WORDS':argv.replace(":", " : "),
                                       'COMP_CWORD':'2' }):
            out = BytesIO()
            with patch.object(sys, 'stdout', out):
                with self.assertRaises(SystemExit):
                    manage(dict(fruit=test_cmd), argv.split())
            self.assertEqual(b'avocado', out.getvalue())
        argv = 'manage.py fruit:av'
        test_cmd = TestCommand()

        with patch.dict('os.environ', {'IKTOMI_AUTO_COMPLETE':'1',
                                       'COMP_WORDS':argv.replace(":", " : "),
                                       'COMP_CWORD':'3' }):
            out = BytesIO()
            with patch.object(sys, 'stdout', out):
                with self.assertRaises(SystemExit):
                    manage(dict(fruit=test_cmd), argv.split())
            self.assertEqual(b'avocado', out.getvalue())
