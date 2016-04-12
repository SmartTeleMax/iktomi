import os
import unittest
from iktomi import web
from iktomi.cli import app
from minimock import Mock
from logging import Logger
import posix


class AppTest(unittest.TestCase):

    def test_close_fds(self):
        result = []
        os.closerange = Mock('closerange')
        os.closerange.mock_returns_func = lambda x, y: result.append((x,y-1))
        app.close_fds()
        self.assertEquals(result, [(3, app.MAXFD-1)])

        result = []
        app.close_fds(100)
        self.assertEquals(result, [(3, 99), (101, app.MAXFD-1)])


    def test_flush_fds(self):
        result = []
        os.fsync = Mock('flush_fds')
        os.fsync.mock_returns_func = lambda x: result.append(x)
        app.flush_fds()
        self.assertEquals(result, range(3, app.MAXFD+1))

    def test_iter_module_files(self):
        files_list = list(app.iter_module_files())
        self.assertTrue(__file__ in files_list)
        app_file = app.__file__[:-1] if app.__file__[-1] in ('c', 'o')\
                                     else app.__file__
        self.assertTrue(app_file in files_list)
