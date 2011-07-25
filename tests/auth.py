# -*- coding: utf-8 -*-

import unittest
from insanities import web
from insanities.auth import CookieAuth, auth_required

__all__ = ['CookieAuthTests']


class MockUser(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)
    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.name == self.name


def get_user_identity(env, login, password):
    return 'user-identity'


def identify_user(env, user_identity):
    return MockUser(name='user name')


class CookieAuthTests(unittest.TestCase):
    def setUp(self):
        self.auth = auth = CookieAuth(get_user_identity, identify_user)
        @web.handler
        def make_env(env, data, nxt):
            env.root = root
            return nxt(env, data)
        def anonymouse(env, data, nxt):
            self.assert_(hasattr(env, 'user'))
            self.assertEqual(env.user, None)
            return web.Response('ok')
        def no_anonymouse(env, data, nxt):
            self.assert_(hasattr(env, 'user'))
            self.assertEqual(env.user, MockUser(name='user name'))
            return web.Response('ok')
        self.app = make_env | web.cases(
            auth.login(),
            auth.logout(),
            auth | web.cases(
                web.match('/a', 'a') | anonymouse,
                web.match('/b', 'b') | auth_required | no_anonymouse,
            ),
        )
        root = web.Reverse.from_handler(self.app)

    def test_anonymouse(self):
        '`Auth` anonymouse access'
        response = web.ask(self.app, '/a')
        self.assertEqual(response.status_int, 200)

        response = web.ask(self.app, '/b')
        self.assertEqual(response.status_int, 303)
        self.assertEqual(response.headers['Location'], '/login?next=/b')
