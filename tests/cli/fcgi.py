# -*- coding: utf-8 -*-
import os
import sys
import unittest
from iktomi.cli.fcgi import Flup
from .fcgi_client import FastCGIClient
import shutil
import signal
from time import sleep
import subprocess
import tempfile


class FlupTests(unittest.TestCase):

    def test_default_init(self):
        flup = Flup("app")
        cwd = os.path.abspath('.')
        self.assertEqual(flup.app, "app")
        self.assertEqual(flup.cwd, cwd)
        self.assertEqual(flup.bind, os.path.join(cwd, 'fcgi.sock'))
        self.assertEqual(flup.logfile, os.path.join(cwd, 'fcgi.log'))
        self.assertEqual(flup.pidfile, os.path.join(cwd, 'fcgi.pid'))


class FlupDaemonTest(unittest.TestCase):

    def setUp(self):
        self.pid = None
        self.temp_dir = tempfile.mkdtemp()
        
        self.manage = os.path.join(self.temp_dir, 'manage.py')
        shutil.copy(os.path.join(os.path.dirname(__file__), 
                                 '../../examples/helloworld/helloworld.py',),
                    self.manage)
        subprocess.Popen([sys.executable, self.manage,
                          'fcgi:start', '--daemonize'])
        sleep(0.5)
        try:
            with open(os.path.join(self.temp_dir, 'fcgi.pid')) as f:
                self.pid = int(f.read().strip())
        except IOError:
            self.fail('Cannot to start the fcgi server')


    def doCleanups(self):
        if self.pid:
            try:
                os.kill(self.pid, signal.SIGKILL)
            except OSError:
                pass
        shutil.rmtree(self.temp_dir)

    def test_daemon(self):
        sock_path = os.path.join(self.temp_dir, 'fcgi.sock')
        result, errors = FastCGIClient(sock_path).make_request()
        self.assertEqual(['hello world'], result)
        self.assertEqual(errors, '')

        with open(self.manage) as f:
            new_code = f.read().replace('world', 'iktomi')
        with open(self.manage, "w") as f:
            f.write(new_code)

        subprocess.Popen([sys.executable, self.manage,
                          'fcgi:restart'])
        sleep(0.5)
        try:

            with open(os.path.join(self.temp_dir, 'fcgi.pid')) as f:
                self.pid = int(f.read().strip())
        except IOError:
            self.fail('Cannot to start the fcgi server')

        result, errors = FastCGIClient(sock_path).make_request()
        self.assertEqual(['hello iktomi'], result)
        self.assertEqual(errors, '')
