# -*- coding: utf-8
import unittest
from webob import Response, Request
from iktomi import web
from iktomi.web.shortcuts import Rule, redirect_to
from iktomi.utils.storage import VersionedStorage


class WebShortcutsTest(unittest.TestCase):

    @property
    def app(self):
        return web.cases(
            web.match('/redirect', 'redirect') | redirect_to('rule1', qs={'page':1}),
            Rule('/rule1',
                 name='rule1',
                 handler=(lambda e, d: Response('rule1')),
            ),
            Rule('/rule2', method='POST', handler=lambda e,d: Response('rule2')),
        )

    @property
    def wsgi_app(self):
        return web.Application(self.app)

    def env_data(self, wsgi_app, path):
        request = Request.blank(path)
        env = VersionedStorage(wsgi_app.env_class, request, wsgi_app.root)
        data = VersionedStorage()
        return env, data

    def test_redirect(self):
        wa = self.wsgi_app
        env, data = self.env_data(wa, '/redirect')
        response = wa.handle(env, data)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers['Location'],
                         'http://localhost/rule1?page=1')

    def test_rule(self):
        wa = self.wsgi_app
        env, data = self.env_data(wa, '/rule1')
        response = wa.handle(env, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, 'rule1')

        env, data = self.env_data(wa, '/rule2')
        response = wa.handle(env, data)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.body, '')
