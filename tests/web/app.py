# -*- coding: utf-8 -*-

__all__ = ['ApplicationTests']

import sys
import unittest
from webob import Response, Request
from webob.exc import HTTPMethodNotAllowed
from iktomi import web
from iktomi.web.app import Application, AppEnvironment
from iktomi.utils.storage import VersionedStorage
from iktomi.utils import cached_property
# import as TA because py.test generates warning about TestApp name
from webtest import TestApp as TA

skip = getattr(unittest, 'skip', lambda x: None)


class ApplicationTests(unittest.TestCase):

    @cached_property
    def app(self):
        def exc(env, data):
            raise HTTPMethodNotAllowed
        return web.cases(
                web.match('/', 'index') | (lambda e,d: Response(body='index')),
                web.match('/500', 'err500') | (lambda e,d: 1+''),
                web.match('/403', 'err403') | exc,
                web.match('/broken_response', 'broken_response') | \
                            (lambda e,d: 0),
            )

    @cached_property
    def wsgi_app(self):
        return Application(self.app)

    def env_data(self, wsgi_app, path):
        request = Request.blank(path)
        env = VersionedStorage(wsgi_app.env_class, request, wsgi_app.root)
        data = VersionedStorage()
        return env, data

    def test_handle(self):
        wa = self.wsgi_app
        env, data = self.env_data(wa, '/')
        response = wa.handle(env, data)
        assert isinstance(response, Response)
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body, 'index')

    def test_returned_none(self):
        wa = self.wsgi_app
        env, data = self.env_data(wa, '/not-found')
        response = wa.handle(env, data)
        assert isinstance(response, Response)
        self.assertEqual(response.status_int, 404)
        self.assertEqual(self.app(env, data), None)

    def test_500(self):
        wa = self.wsgi_app

        errors = []
        def handle_error(env):
            _, e, _ = sys.exc_info()
            errors.append(e)
        wa.handle_error = handle_error

        env, data = self.env_data(wa, '/500')
        response = wa.handle(env, data)
        assert isinstance(response, Response)
        self.assertEqual(response.status_int, 500)
        assert isinstance(errors[0], TypeError)
        self.assertRaises(TypeError, self.app, env, data)

    def test_broken_response(self):
        wa = self.wsgi_app

        errors = []
        def handle_error(env):
            _, e, _ = sys.exc_info()
            errors.append(e)
        wa.handle_error = handle_error

        #env, data = self.env_data(wa, '/none')
        environ = {
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '80',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '',
            'PATH_INFO': '/broken_response',
        }
        def start_response(status, headers):
            self.assertTrue(status.startswith('500'))
        wa(environ, start_response)
        self.assertTrue(isinstance(errors[0], TypeError))

    def test_wsgi(self):
        testapp = TA(self.wsgi_app)
        self.assertEqual(testapp.get('/').body, 'index')

    def test_env_class(self):
        class AppEnv(AppEnvironment): pass
        wa = Application(self.app, AppEnv)
        assert wa.env_class == AppEnv

