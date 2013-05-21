# -*- coding: utf-8 -*-

import os
import sys
import time
import errno
import signal
import logging
logger = logging.getLogger(__name__)

from .base import Cli
from iktomi.utils.system import safe_makedirs, doublefork


def flup_fastcgi(wsgi_app, bind, cwd=None, pidfile=None, logfile=None,
                 daemonize=False, umask=None, **params):
    if params.pop('preforked', False):
        from flup.server import fcgi_fork as fcgi
    else:
        from flup.server import fcgi
    if daemonize:
        if os.path.isfile(pidfile):
            with open(pidfile, 'r') as f:
                pid = int(f.read())
            try:
                os.kill(pid, 0)
                sys.exit('Cant start fcgi b.c. process %r is running' % pid)
            except OSError, err:
                if err.errno != errno.ESRCH:
                    raise
                logger.info('Pidfile was pointing to nonexistent process %r' % \
                            pid)
        doublefork(pidfile, logfile, cwd, umask)
    logger.info('Starting FastCGI server (flup), current working dir %r' % cwd)
    fcgi.WSGIServer(wsgi_app, bindAddress=bind, umask=umask,
                    debug=False, **params).run()


class Flup(Cli):

    def __init__(self, app, bind='', logfile=None, pidfile=None,
                 cwd='.', umask=002, fastcgi_params=None):
        self.app = app
        self.cwd = os.path.abspath(cwd)
        if ':' in bind:
            host, port = bind.split(':')
            port = int(port)
        else:
            bind = os.path.abspath(bind or os.path.join(self.cwd, 'fcgi.sock'))
            safe_makedirs(bind)
        self.bind = bind
        self.umask = umask
        self.logfile = logfile or os.path.join(self.cwd, 'fcgi.log')
        self.pidfile = pidfile or os.path.join(self.cwd, 'fcgi.pid')
        self.fastcgi_params = fastcgi_params or {}

    def command_start(self, daemonize=False):
        if daemonize:
            safe_makedirs(self.logfile, self.pidfile)
        flup_fastcgi(self.app, bind=self.bind, pidfile=self.pidfile,
                     logfile=self.logfile, daemonize=daemonize,
                     cwd=self.cwd, umask=self.umask, **self.fastcgi_params)

    def _wait_pid(self, pid):
        try:
            p, status = os.waitpid(pid, os.WNOHANG)
            if p != 0:
                if os.WIFSIGNALED(status):
                    logger.warning('Fcgi (PID=%d) killed with signal %d',
                                   p, os.WTERMSIG(status))
                    sys.exit()
                elif os.WIFEXITED(status):
                    code = os.WEXITSTATUS(status)
                    logger.log(logging.WARNING if code else logging.INFO,
                               'Fcgi (PID=%d) exited with status %d',
                               p, code)
                    sys.exit(code)
        except OSError, exc:
            # "No such process" is OK, silently ignore it. The rest
            # should be logged at least.
            if exc.errno == errno.ECHILD:
                logger.info('Fcgi (PID=%d) disappeared' % pid)
                sys.exit(0)
            raise

    def command_stop(self):
        if self.pidfile:
            if not os.path.exists(self.pidfile):
                sys.exit('Pidfile %r is absent\n' % self.pidfile)
            with open(self.pidfile) as pidfile:
                pid = int(pidfile.read())
            os.kill(pid, signal.SIGINT)
            time.sleep(2)
            self._wait_pid(pid)
            os.kill(pid, signal.SIGKILL)
            time.sleep(3)
            self._wait_pid(pid)
        sys.exit('No pidfile provided\n')

    def command_restart(self):
        self.command_stop()
        time.sleep(1)
        self.command_start()
