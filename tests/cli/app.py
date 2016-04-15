import os
import sys
import unittest
import shutil
from iktomi import web
from iktomi.cli import app
from logging import Logger
from cStringIO import StringIO
import signal
from time import sleep
import subprocess
import urllib2


try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

class AppTest(unittest.TestCase):

    def test_iter_module_files(self):
        files_list = list(app.iter_module_files())
        self.assertTrue(__file__ in files_list)
        app_file = app.__file__[:-1] if app.__file__.endswith(('.pyc', '.pyo'))\
                                     else app.__file__
        self.assertTrue(app_file in files_list)


class WaitForChangeTest(unittest.TestCase):

    def setUp(self):
        os.mkdir('temp_dir')
        self.f = open('temp_dir/tempfile', 'w')

    def doCleanups(self):
        self.f.close()
        if os.path.isdir('temp_dir'):
            shutil.rmtree('temp_dir')

    def test_wait_for_code_changes(self):
        result = []

        r, w = os.pipe()
        pid = os.fork()

        if pid:
            os.close(w)
            sleep(1)
            self.f.write('something')
            self.f.flush()
            sleep(1)
            r = os.fdopen(r)
            self.assertEqual('Changes in file "temp_dir/tempfile"', r.read())
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
        else:
            os.close(r)
            w = os.fdopen(w, 'w')
            def writeback_and_stop(message, filename, *args, **kwargs):
                w.write(message % filename)
                w.close()

            Logger.info = Mock(side_effect=writeback_and_stop)
            app.wait_for_code_change(extra_files=('temp_dir/tempfile',))
            os._exit(0)


class CliAppTest(unittest.TestCase):

    def setUp(self):
        webapp = web.cases(
            web.match('/', 'index') | (lambda e, d: 'hello')
        )
        self.app = app.App(webapp, shell_namespace={'hello':'world'})

    def test_command_shell(self):
        inp = StringIO('print hello')
        out = StringIO()
        with patch.object(sys, 'stdin', inp):
            with patch.object(sys, 'stdout', out):
                self.app.command_shell()
        self.assertEqual(out.getvalue(), '>>> world\n>>> ')


class WebAppServerTest(unittest.TestCase):

    def setUp(self):
        os.mkdir('temp_dir')
        self.manage = os.path.join('temp_dir', 'manage.py')
        shutil.copy(os.path.join(os.path.dirname(__file__), 'helloworld.py',),
                    'temp_dir/manage.py')
        environ = os.environ.copy()
        environ['COVERAGE_PROCESS_START'] = '/home/ilya/iktomi/current/iktomi/setup.cfg'
        self.server = subprocess.Popen([sys.executable, self.manage], env=environ)
        sleep(0.5)

    def doCleanups(self):
        shutil.rmtree('temp_dir')
        self.server.send_signal(signal.SIGINT) # we MUST exit from subprocess
                                               # normal way to perform coverage correctly
        self.server.wait()

    def test_web_app_server(self):
        response = urllib2.urlopen('http://localhost:11111')
        self.assertEqual("hello world", response.read())
        response.close()
        with open(self.manage) as f:
            new_code = f.read().replace('world', 'iktomi')
        with open(self.manage, "w") as f:
            f.write(new_code)
        sleep(2) # wait until code changes
        response = urllib2.urlopen('http://localhost:11111')
        self.assertEqual("hello iktomi", response.read())
        response.close()
