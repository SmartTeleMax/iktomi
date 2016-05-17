# -*- coding: utf-8 -*-
import six
import sys
import os
import datetime

__all__ = ['manage']


class CommandNotFound(AttributeError): pass
class ConverterError(Exception): pass


def manage(commands, argv=None, delim=':'):
    '''
    Parses argv and runs neccessary command. Is to be used in manage.py file.

    Accept a dict with digest name as keys and instances of
    :class:`Cli<iktomi.management.commands.Cli>`
    objects as values.

    The format of command is the following::

        ./manage.py digest_name:command_name[ arg1[ arg2[...]]][ --key1=kwarg1[...]]

    where command_name is a part of digest instance method name, args and kwargs
    are passed to the method. For details, see
    :class:`Cli<iktomi.management.commands.Cli>` docs.
    '''

    commands = {(k.decode('utf-8') if isinstance(k, six.binary_type) else k): v
                for k, v in commands.items()}

    # Default django autocompletion script is registered to manage.py
    # We use the same name for this script and it seems to be ok
    # to implement the same interface
    def perform_auto_complete(commands):
        from .lazy import LazyCli
        cwords = os.environ['COMP_WORDS'].split()[1:]
        cword = int(os.environ['COMP_CWORD'])

        try:
            curr = cwords[cword - 1]
        except IndexError:
            curr = ''

        suggest = []
        if len(cwords) > 1 and cwords[0] in commands.keys():
            value = commands[cwords[0]]
            if isinstance(value, LazyCli):
                value = value.get_digest()

            for cmd_name, _ in value.get_funcs():
                cmd_name = cmd_name[8:]
                suggest.append(cmd_name)
            if curr == ":":
                curr = ''
        else:
            suggest += list(commands.keys()) + [x+":" for x in commands.keys()]
        suggest.sort()
        output = u" ".join(filter(lambda x: x.startswith(curr), suggest))
        sys.stdout.write(output)

    auto_complete = 'IKTOMI_AUTO_COMPLETE' in os.environ or \
                    'DJANGO_AUTO_COMPLETE' in os.environ
    if auto_complete:
        perform_auto_complete(commands)
        sys.exit(0)

    argv = sys.argv if argv is None else argv
    if len(argv) > 1:
        cmd_name = argv[1]
        raw_args = argv[2:]
        args, kwargs = [], {}
        # parsing params
        for item in raw_args:
            if item.startswith('--'):
                splited = item[2:].split('=', 1)
                if len(splited) == 2:
                    k,v = splited
                elif len(splited) == 1:
                    k,v = splited[0], True
                kwargs[k] = v
            else:
                args.append(item)

        # trying to get command instance
        if delim in cmd_name:
            digest_name, command = cmd_name.split(delim)
        else:
            digest_name = cmd_name
            command = None
        try:
            digest = commands[digest_name]
        except KeyError:
            _command_list(commands)
            sys.exit('ERROR: Command "{}" not found'.format(digest_name))
        try:
            if command is None:
                if isinstance(digest, Cli):
                    help_ = digest.description(argv[0], digest_name)
                    sys.stdout.write(help_)
                    sys.exit('ERROR: "{}" command digest requires command name'\
                                .format(digest_name))
                digest(*args, **kwargs)
            else:
                digest(command, *args, **kwargs)
        except CommandNotFound:
            help_ = digest.description(argv[0], digest_name)
            sys.stdout.write(help_)
            sys.exit('ERROR: Command "{}:{}" not found'.format(digest_name, command))
    else:
        _command_list(commands)
        sys.exit('Please provide any command')

def _command_list(commands):
    sys.stdout.write(u'Commands:\n')
    for k in commands.keys():
        sys.stdout.write(k)
        sys.stdout.write(u'\n')


class Cli(object):
    'Base class for all command digests'

    def _fix_docstring(self, doc, indent=0):
        doc = doc.lstrip('\n').rstrip()
        doc = doc.split('\n\n')[0].rstrip(':')
        doc =  '\n'.join('\t'*indent + x.lstrip()
                         for x in doc.splitlines())
        doc += '\n'
        return doc

    def get_funcs(self):
        return [(attr, getattr(self, attr))
                 for attr in dir(self)
                 if attr.startswith('command_')]

    def description(self, argv0='manage.py', command=None):
        '''Description outputed to console'''
        command = command or self.__class__.__name__.lower()
        import inspect
        _help = u''
        _help += u'{}\n'.format(command)
        if self.__doc__:
            _help += self._fix_docstring(self.__doc__) +'\n'
        else:
            _help += u'{}\n'.format(command)

        funcs = self.get_funcs()
        funcs.sort(key=lambda x: six.get_function_code(x[1]).co_firstlineno)

        for attr, func in funcs:
            func = getattr(self, attr)
            comm = attr.replace('command_', '', 1)
            args = inspect.getargspec(func).args[1:]
            args = (' [' + '] ['.join(args) + ']') if args else ''

            _help += "\t{} {}:{}{}\n".format(
                            argv0, command, comm, args)

            if func.__doc__:
                _help += self._fix_docstring(func.__doc__, 2)
        return _help

    def __call__(self, command_name, *args, **kwargs):
        if command_name == 'help':
            sys.stdout.write(self.description())
        elif hasattr(self, 'command_'+command_name):
            try:
                getattr(self, 'command_'+command_name)(*args, **kwargs)
            except ConverterError as e:
                sys.stderr.write(u'One of the arguments for '
                                 u'command "{}" is wrong:\n'.format(command_name))
                sys.exit(e)
        else:
            raise CommandNotFound()


class argument(object):
    'Decorator. Helps to define desired argument types'

    def __init__(self, arg_id, *validators, **kwargs):
        assert type(arg_id) in (int, str), \
            'First argument of argument ({!r}) decorator must be "str" '\
            'or "int" type'.format(arg_id)
        self.arg_id = arg_id
        self.validators = validators
        self.required = kwargs.get('required', True)

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            args = list(args)
            if isinstance(self.arg_id, int):
                try:
                    arg = args[self.arg_id]
                except IndexError:
                    raise ConverterError('Total positional args = {:d}, '
                        'but you apply converter for {:d} argument '
                        '(indexing starts from 0)'.format(len(args), self.arg_id))
                arg = self.convert(arg)
                args[self.arg_id] = arg
            elif isinstance(self.arg_id, str):
                arg = kwargs.get(self.arg_id)
                if arg:
                    arg = self.convert(arg)
                    kwargs[self.arg_id] = arg
                if not arg and self.required:
                    raise ConverterError('Keyword argument "{}" is required'\
                                            .format(self.arg_id))
            return func(*args, **kwargs)
        return wrapper

    def convert(self, arg):
        for v in self.validators:
            arg = v(arg)
        return arg

    @staticmethod
    def to_int(value):
        try:
            return int(value)
        except Exception:
            raise ConverterError('Cannot convert {!r} to int'.format(value))

    @staticmethod
    def to_date(value):
        try:
            return datetime.datetime.strptime(value, '%d/%m/%Y').date()
        except Exception:
            raise ConverterError('Cannot convert {!r} to date, please provide '
                                 'string in format "dd/mm/yyyy"'.format(value))
