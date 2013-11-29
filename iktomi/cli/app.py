# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import threading
from os import path
from itertools import chain

from .base import Cli, CommandNotFound

__all__ = ['App']


logger = logging.getLogger(__name__)


try:
    MAXFD = os.sysconf("SC_OPEN_MAX")
except:
    MAXFD = 256


def close_fds(but=None):
    if but is None:
        os.closerange(3, MAXFD)
        return
    os.closerange(3, but)
    os.closerange(but + 1, MAXFD)


def flush_fds():
    for fd in range(3, MAXFD + 1):
        try:
            os.fsync(fd)
        except OSError:
            pass


class App(Cli):
    'Development application'
    format = '%(levelname)s [%(name)s] %(message)s'

    def __init__(self, app, shell_namespace=None, extra_files=None, bootstrap=None):
        self.app = app
        self.shell_namespace = shell_namespace or {}
        self.extra_files = extra_files
        self.bootstrap = bootstrap

    def command_serve(self, host='', port='8000', level='debug'):
        logging.basicConfig(level=getattr(logging, level.upper()), format=self.format)
        if self.bootstrap:
            logger.info('Bootstraping...')
            self.bootstrap()
        try:
            server_thread = DevServerThread(host, port, self.app)
            server_thread.start()

            wait_for_code_change(extra_files=self.extra_files)

            server_thread.running = False
            server_thread.join()
            logger.info('Reloading...')

            # Smart reload of current process.
            # Main goal is to reload all modules
            # NOTE: For exec syscall we need to flush and close all fds manually
            flush_fds()
            close_fds()
            os.execvp(sys.executable, [sys.executable] + sys.argv)
        except KeyboardInterrupt:
            logger.info('Stoping dev-server...')
            server_thread.running = False
            server_thread.join()
            sys.exit()

    def command_shell(self):
        from code import interact
        interact('Namespace %r' % self.shell_namespace,
                 local=self.shell_namespace)


class DevServerThread(threading.Thread):

    def __init__(self, host, port, app):
        from wsgiref.simple_server import make_server, WSGIServer, \
                WSGIRequestHandler
        self.host = host
        self.port = port

        class DevServer(WSGIServer):
            timeout = 0.2


        class RequestHandler(WSGIRequestHandler):
            def address_string(slf):
                # getfqdn sometimes is very slow
                return '%s:%s' % (host, port)

            def log_message(self, format, *args):
                logger.info("%s - - [%s] %s",
                            self.client_address[0],
                            self.log_date_time_string(),
                            format%args)

        try:
            self.port = int(port)
        except ValueError:
            raise ValueError('Please provide valid port value insted of "%s"' % port)
        self.running = True
        self.server = make_server(self.host, self.port, app, server_class=DevServer,
                                  handler_class=RequestHandler)
        super(DevServerThread, self).__init__()

    def run(self):
        logger.info('Devserver is running on port %s\n', self.port)
        while self.running:
            self.server.handle_request()


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


def wait_for_code_change(extra_files=None, interval=1):
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
            elif mtime > old_time:
                logger.info('Changes in file "%s"', filename)
                return
        time.sleep(interval)

