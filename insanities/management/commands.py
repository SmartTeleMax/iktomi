# -*- coding: utf-8 -*-

import sys
from os import path

from . import CommandNotFound

__all__ = ['server']


class CommandDigest(object):

    def default(self, *args, **kwargs):
        '''This method will be called if command_name in __call__ is None'''
        print self.description()

    def description(self):
        '''Description outputed to console'''
        _help = self.__class__.__doc__
        for k in dir(self):
            if k.startswith('command_'):
                _help += '\n'
                _help += getattr(self, k).__doc__
        return _help

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

    def __init__(self, app):
        self.app = app

    def command_serve(self, host='', port='8000'):
        '''python manage.py server:serve [host] [port]'''
        import logging
        logging.basicConfig(level=logging.DEBUG)
        from wsgiref.simple_server import make_server
        from insanities.web.wsgi import WSGIHandler
        try:
            port = int(port)
        except ValueError:
            raise ValueError('Please provide valid port value insted of "%s"' % port)
        server = make_server(host, port, WSGIHandler(self.app))
        try:
            logging.info('Insanities server is running on port %s\n' % port)
            server.serve_forever()
        except KeyboardInterrupt:
            pass

    def command_debug(self, url):
        '''python manage.py server:debug url'''
        import pdb
        from ..web.http import RequestContext
        rctx = RequestContext.blank(url)
        try:
            self.app(rctx)
        except Exception, e:
            pdb.post_mortem(e)
