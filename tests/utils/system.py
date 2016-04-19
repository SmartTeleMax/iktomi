# -*- coding: utf-8 -*-

import os
import shutil
import signal
import tempfile
import time
import unittest

from iktomi.utils.system import (
    is_running, safe_makedirs, terminate, doublefork,
)


class SystemCases(unittest.TestCase):

    @unittest.skipIf(os.getuid()==0, "Test mustn't be run as superuser")
    def test_is_running_no_access(self):
        with self.assertRaises(OSError):
            is_running(1)

    def test_is_running_true(self):
        pid = os.fork()

        if pid:
            self.assertTrue(is_running(pid))

            # Cleaning up
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)

        else:
            time.sleep(1)
            os._exit(0)

    def test_is_running_false(self):
        pid = os.fork()

        if pid:
            os.waitpid(pid, 0)
            self.assertFalse(is_running(pid))

        else:
            os._exit(0)

    def test_terminate_child_true(self):
        pid = os.fork()
        if pid:
            started = time.time()
            success = terminate(pid, signal.SIGKILL, 0.5)
            finished = time.time()
            self.assertTrue(success)
            self.assertFalse(is_running(pid))
            self.assertLess(finished-started, 1)
        else:
            time.sleep(3)
            os._exit(os.EX_OK)

    def test_terminate_alien_true(self):
        _, pidfile = tempfile.mkstemp()
        child_pid = os.fork()
        if child_pid:
            time.sleep(0.1)
            with open(pidfile) as fp:
                pid = int(fp.read())
            self.assertTrue(is_running(pid))
            started = time.time()
            success = terminate(pid, signal.SIGKILL, 0.5)
            finished = time.time()
            self.assertTrue(success)
            self.assertFalse(is_running(pid))
            self.assertLess(finished-started, 1)
        else:
            doublefork(pidfile, '/dev/null', '.', 0)
            time.sleep(3)
            os._exit(os.EX_OK)

    def test_terminate_false(self):
        pid = os.fork()

        if pid:
            started = time.time()
            success = terminate(pid, 0, 0.5)
            finished = time.time()
            self.assertFalse(success)
            self.assertTrue(is_running(pid))
            self.assertLess(finished-started, 1)

            # Cleaning up
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)

        else:
            time.sleep(3)
            os._exit(os.EX_OK)

    def test_safe_makedirs(self):
        tmp = tempfile.mkdtemp()
        dir_path = os.path.join(tmp, 'aa', 'bb')
        file_path = os.path.join(dir_path, 'file.ext')
        safe_makedirs(file_path)
        self.assertTrue(os.path.isdir(dir_path))
        # Must not fail when is alreay exists
        safe_makedirs(file_path)

        # Cleaning up
        shutil.rmtree(tmp)
