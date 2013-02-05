# -*- coding: utf-8 -*-

import os
import logging
import signal
from os import path
logger = logging.getLogger(__name__)

from . import wsgiservers
from .base import Cli


class Flup(Cli):
    'Flup FCGI application'

    def __init__(self, app):
        self.app = app

    def command_start(self, bind='', log=None, pid=None,
                      daemonize=False, preforked=False):
        wsgiservers.flup_fastcgi(self.app, bind=bind, pidfile=pid, logfile=log,
                                 daemon=daemonize, preforked=preforked)
    def command_stop(self):
        pidfile_name = path.join(path.abspath('.'), 'run/fcgi.pid')
        if not path.exists(pidfile_name):
            print 'Pid file is absent'
            return
        with open(pidfile_name) as pidfile:
            pid = int(pidfile.read())
            os.kill(pid, signal.SIGTERM)

    def command_restart(self):
        self.command_stop()
        self.command_start()
