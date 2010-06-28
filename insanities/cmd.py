# -*- coding: utf-8 -*-

import sys
from os import path


from mage import CommandDigest, CommandNotFound


class server(CommandDigest):
    '''
    Development server:

        $ python manage.py server:serve
    '''

    def __init__(self, app):
        self.app = app

    def command_serve(self, host='', port='8000', level='debug'):
        '''python manage.py server:serve [host] [port]'''
        import logging
        logging.basicConfig(level=getattr(logging, level.upper()))
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
        from ..web.core import RequestContext, STOP
        rctx = RequestContext.blank(url)
        try:
            result = self.app(rctx)
            if result is STOP:
                sys.exit('%r NotFound' % url)
            else:
                sys.stdout.write('=============================\n')
                sys.stdout.write('%r %s\n' % (url, rctx.response.status))
                sys.stdout.write('=============================\n')
                sys.stdout.write('Data:\n')
                for k,v in rctx.data.as_dict().items():
                    sys.stdout.write('%r : %r\n' % (k, v))
        except Exception, e:
            pdb.post_mortem(e)

