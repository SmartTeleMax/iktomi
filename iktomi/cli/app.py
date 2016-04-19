# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import threading
from itertools import chain

from .base import Cli

__all__ = ['App']


logger = logging.getLogger(__name__)


try:
    MAXFD = os.sysconf("SC_OPEN_MAX")
except: # pragma: no cover
    MAXFD = 256


def flush_fds():
    for fd in range(3, MAXFD + 1):
        try:
            os.fsync(fd)
        except OSError:
            pass


class App(Cli):
    '''
    Development application

    :param app: iktomi app
    :param shell_namespace: dict with initial namespace for shell command
    :param extra_files: extra files to watch and reload if they are changed
    :param bootstrap: bootstrap function before called dev server is being runned
    '''
    format = '%(levelname)s [%(name)s] %(message)s'

    def __init__(self, app, shell_namespace=None, extra_files=None, bootstrap=None):
        self.app = app
        self.shell_namespace = shell_namespace or {}
        self.extra_files = extra_files
        self.bootstrap = bootstrap

    def command_serve(self, host='', port='8000', level='debug'):
        '''
        Run development server with automated reload on code change::

            ./manage.py app:serve [host] [port] [level]
        '''
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
            flush_fds()
            pid = os.fork()
            # We need to fork before `execvp` to perform code reload
            # correctly, because we need to complete python destructors and
            # `atexit`.
            # This will save us from problems of incorrect exit, such as:
            # - unsaved data in data storage, which does not write data
            # on hard drive immediatly
            # - code, that can't be measured with coverage tool, because it uses
            # `atexit` handler to save coverage data
            # NOTE: we using untipical fork-exec scheme with replacing
            # the parent process(not the child) to preserve PID of proccess
            # we use `pragma: no cover` here, because parent process cannot be
            # measured with coverage since it is ends with `execvp`
            if pid: # pragma: no cover
                os.closerange(3, MAXFD)
                os.waitpid(pid, 0)
                # reloading the code in parent process
                os.execvp(sys.executable, [sys.executable] + sys.argv)
            else:
                # we closing our recources, including file descriptors
                # and performing `atexit`.
                sys.exit()
        except KeyboardInterrupt:
            logger.info('Stoping dev-server...')
            server_thread.running = False
            server_thread.join()
            sys.exit()

    def command_shell(self):
        '''
        Shell command::

            ./manage.py app:shell

        Executed with `self.shell_namespace` as local variables namespace.
        '''
        from code import interact
        interact('Namespace {!r}'.format(self.shell_namespace),
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
                return '{}:{}'.format(host, port)

            def log_message(self, format, *args):
                logger.info("%s - - [%s] %s",
                            self.client_address[0],
                            self.log_date_time_string(),
                            format % args)

        try:
            self.port = int(port)
        except ValueError:
            raise ValueError(
                'Please provide valid port value insted of "{}"'.format(port))
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
            while not os.path.isfile(filename): # pragma: no cover
                # NOTE: this code is needed for the cases of importing
                # from archive or custom importers
                # for example, if we importing from archive foo.zip
                # module named zipped, then this zipped.__file__ will equal
                # to foo.zip/zipped.py, and os.path.dirname will give us
                # file, not directory.
                # It is marked as pragma: no cover, because this code was taken
                # from werkzeug and we believe that it is tested
                filename = os.path.dirname(filename)
                if not filename:
                    break
            else:
                if filename.endswith(('.pyc', '.pyo')):
                    filename = filename[:-1]
                yield filename


def wait_for_code_change(extra_files=None, interval=1):
    mtimes = {}
    while 1:
        for filename in chain(iter_module_files(), extra_files or ()):
            try:
                mtime = os.stat(filename).st_mtime
            except OSError: # pragma: no cover
                # this is cannot be guaranteed covered by coverage because of interpreter optimization
                # see https://bitbucket.org/ned/coveragepy/issues/198/continue-marked-as-not-covered#comment-4052311

                continue

            old_time = mtimes.get(filename)
            if old_time is None:
                mtimes[filename] = mtime
            elif mtime > old_time:
                logger.info('Changes in file "%s"', filename)
                return
        time.sleep(interval)

