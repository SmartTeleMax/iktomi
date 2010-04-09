# -*- coding: utf-8 -*-

import sys
from os import path

from . import CommandNotFound

__all__ = ['server']


class CommandDigest(object):

    def __init__(self, cfg):
        '''Do not override init, use prepair instead'''
        self.prepair(cfg)

    def prepair(self, cfg):
        '''Here you can do any initial tasks'''
        self.cfg = cfg

    def default(self, *args, **kwargs):
        '''This method will be called if command_name in __call__ is None'''
        sys.stdout.write(self.__class__.__doc__)

    def __call__(self, command_name, *args, **kwargs):
        if command_name is None:
            self.default(*args, **kwargs)
        elif command_name == 'help':
            sys.stdout.write(self.__doc__)
            for k in self.__dict__.keys():
                if k.startswith('command_'):
                    sys.stdout.write(k.__doc__)
        elif hasattr(self, 'command_'+command_name):
            getattr(self, 'command_'+command_name)(*args, **kwargs)
        else:
            sys.stdout.write(self.__class__.__doc__)
            raise CommandNotFound()


class server(CommandDigest):
    '''
    Development server:

        $ python manage.py server:serve
    '''

    def command_serve(self, host='', port='8000'):
        '''python manage.py serve [host] [port]'''
        import logging
        from app import app
        logging.basicConfig(level=logging.DEBUG)
        from wsgiref.simple_server import make_server
        from insanities.web.wsgi import WSGIHandler
        try:
            port = int(port)
        except ValueError:
            raise ValueError('Please provide valid port value insted of "%s"' % port)
        server = make_server(host, port, WSGIHandler(app))
        try:
            logging.debug('Insanities server is running on port %s\n' % port)
            server.serve_forever()
        except KeyboardInterrupt:
            pass

    def command_map(self):
        from app import app
        for chain in app.chains:
            print repr(chain)

