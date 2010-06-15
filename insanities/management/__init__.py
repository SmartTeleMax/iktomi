# -*- coding: utf-8 -*-

import sys
from sys import argv


class CommandNotFound(AttributeError): pass


def manage(commands):
    '''
    Parses argv and runs neccessary command. Is to be used in manage.py file.

    Accept a dict with digest name as keys and instances of
    :class:`CommandDigest<insanities.management.commands.CommandDigest>`
    objects as values.

    The format of command is the following::

        ./manage.py digest_name:command_name[ arg1[ arg2[...]]][ --key1=kwarg1[...]]

    where command_name is a part of digest instance method name, args and kwargs
    are passed to the method. For details, see
    :class:`CommandDigest<insanities.management.commands.CommandDigest>` docs.
    '''
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
                else:
                    sys.exit('Error while parsing argument "%s"' % item)
                kwargs[k] = v
            else:
                args.append(item)

        # trying to get command instance
        if ':' in cmd_name:
            digest_name, command = cmd_name.split(':')
        else:
            digest_name = cmd_name
            command = None
        try:
            digest = commands[digest_name]
        except KeyError:
            print 'Commands:'
            for k in commands.keys():
                print k
            sys.exit('Command "%s" not found' % digest_name)
        try:
            digest(command, *args, **kwargs)
        except CommandNotFound:
            print commands[digest_name].description()
            sys.exit('Command "%s:%s" not found' % (digest_name, command))
    else:
        sys.exit('Please provide any command')
