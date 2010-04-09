# -*- coding: utf-8 -*-

import sys
from sys import argv


class CommandNotFound(AttributeError): pass


def manage(cfg, commands):
    if len(argv) > 1:
        cmd_name = argv[1]
        raw_args = argv[2:]
        args, kwargs = [], {}
        # parsing params
        #XXX: it's good idea to use optparse
        for item in raw_args:
            if '=' in item:
                try:
                    k,v = item.split('=')
                except ValueError:
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
            digest_class = getattr(commands, digest_name)
        except AttributeError:
            sys.exit('Command "%s" not found' % digest_name)
        digest = digest_class(cfg)
        try:
            digest(command, *args, **kwargs)
        except CommandNotFound:
            sys.exit('Command "%s.%s" not found' % (digest_name, command))
    else:
        sys.exit('Please provide any command')
