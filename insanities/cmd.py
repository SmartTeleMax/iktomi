# -*- coding: utf-8 -*-

import sys
import os
import threading
import logging
logger = logging.getLogger(__name__)
from os import path


from mage import CommandDigest, CommandNotFound


class server(CommandDigest):
    '''
    Development server:

        $ python manage.py server:serve
    '''

    format = '[%(name)s::%(levelname)s] %(message)s'

    def __init__(self, app_name):
        self.app_name = app_name

    def command_serve(self, host='', port='8000', level='debug'):
        '''python manage.py server:serve [host] [port]'''
        logging.basicConfig(level=getattr(logging, level.upper()), format=self.format)
        try:
            server_thread = DevServerThread(host, port, self.app_name)
            server_thread.start()
            for filename in reloader_loop():
                server_thread.running = False
                server_thread.join()
                logger.info('File "%s" is changed. Reloading...' % filename)
                # Smart reload of current process.
                # Main goal is to reload all modules
                os.execvp(sys.executable, [sys.executable] + sys.argv)
                server_thread = DevServerThread(host, port, self.app_name)
                server_thread.start()
        except KeyboardInterrupt:
            logger.info('shuting down')
            server_thread.running = False
            server_thread.join()
            sys.exit()

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


class DevServerThread(threading.Thread):

    def __init__(self, host, port, app_name):
        from wsgiref.simple_server import make_server, WSGIServer
        from insanities.web.wsgi import WSGIHandler
        names = app_name.split('.')
        app = getattr(__import__('.'.join(names[:-1]), None, None, ['*']), names[-1])
        self.host = host
        self.port = port
        class DevServer(WSGIServer):
            timeout = 0.2
        try:
            self.port = int(port)
        except ValueError:
            raise ValueError('Please provide valid port value insted of "%s"' % port)
        self.running = True
        self.server = make_server(self.host, self.port, WSGIHandler(app), server_class=DevServer)
        super(DevServerThread, self).__init__()

    def run(self):
        logger.info('Insanities server is running on port %s\n' % self.port)
        while self.running:
            self.server.handle_request()
        self.server.socket.close()


# All reloader utils are taken from werkzeug
def iter_module_files():
    for module in sys.modules.values():
        filename = getattr(module, '__file__', None)
        if filename:
            while not os.path.isfile(filename):
                filename = os.path.dirname(filename)
                if not filename:
                    break
            else:
                if filename[-4:] in ('.pyc', '.pyo'):
                    filename = filename[:-1]
                yield filename


def reloader_loop(extra_files=None, interval=1):
    import time
    from itertools import chain
    mtimes = {}
    while 1:
        for filename in chain(iter_module_files(), extra_files or ()):
            try:
                mtime = os.stat(filename).st_mtime
            except OSError:
                continue

            old_time = mtimes.get(filename)
            if old_time is None:
                mtimes[filename] = mtime
                continue
            elif mtime > old_time:
                mtimes[filename] = mtime
                yield filename
        time.sleep(interval)
