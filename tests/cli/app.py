import os
import unittest
from iktomi import web
from iktomi.cli import app
from logging import Logger
import signal
from time import sleep

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


class AppTest(unittest.TestCase):

    def test_iter_module_files(self):
        files_list = list(app.iter_module_files())
        self.assertTrue(__file__ in files_list)
        app_file = app.__file__[:-1] if app.__file__[-1] in ('c', 'o')\
                                     else app.__file__
        self.assertTrue(app_file in files_list)


class WaitForChangeTest(unittest.TestCase):

    def setUp(self):
        os.mkdir('temp_dir')
        self.f = open('temp_dir/tempfile', 'w')

    def tearDown(self):
        self.f.close()
        os.unlink('temp_dir/tempfile')
        os.rmdir('temp_dir')

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
                os._exit(0)

            Logger.info = Mock(side_effect= writeback_and_stop)
            app.wait_for_code_change(extra_files=('temp_dir/tempfile',))
