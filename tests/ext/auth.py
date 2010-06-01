# -*- coding: utf-8 -*-

import unittest
from insanities.web import *
from insanities.web.filters import *
from insanities.web.http import RequestContext
from insanities.ext.cache import cache_dict
from insanities.ext.auth import CookieAuth
from insanities.ext.jinja2 import jinja_env


class MockUser(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)


def user_by_credential(rctx, **kw):
    return 1


def user_by_id(rctx, id):
    return MockUser(name='user name')


class AuthTest(unittest.TestCase):

    def test_login_logout(self):
        'Login and Logout process'
        auth = CookieAuth(user_by_credential, user_by_id)

        def logout(r):
            self.assertEqual(len(r.vals.session_storage.cache), 0)

        def login(r):
            self.assertEqual(len(r.vals.session_storage.cache), 1)

        app = cache_dict() | jinja_env() | Map(
            auth.login_handler | login,
            auth.logout_handler | logout,
            auth | Map(
                match('/', 'index')
            )
        )
        rctx = RequestContext.blank('/login', login='user name', password='12345')
        rctx = app(rctx)

        self.assert_(rctx.response.headers.get('Set-Cookie'))

        rctx = RequestContext.blank('/logout', login='user name')
        rctx = app(rctx)

    def test_anonym_unauth(self):
        'Anonym and unathorized access'

        def anonym(r):
            self.assert_(r.vals.user is None)

        auth = CookieAuth(user_by_credential, user_by_id)
        app = cache_dict() | jinja_env() | Map(
            auth.login_handler,
            auth.logout_handler,
            auth | Map(
                match('/', 'index') | anonym,
            )
        )

        rctx = RequestContext.blank('/')
        rctx = app(rctx)

        def view(r):
            r.response.write('aaaa')

        app = cache_dict() | jinja_env() | Map(
            auth.login_handler,
            auth.logout_handler,
            auth | auth.login_required | Map(
                match('/', 'index') | view
            )
        )
        rctx = RequestContext.blank('/')
        self.assertEqual(app(rctx).response.status_int, 303)
        self.assertEqual(app(rctx).response.headers.get('Location'), '/login?next=/')

    def test_auth(self):
        'Authorized access'
        auth = CookieAuth(user_by_credential, user_by_id)
        def user(r):
            self.assertEqual(r.vals.user.name, 'user name')
        app = cache_dict() | jinja_env() | Map(
            auth.login_handler,
            auth.logout_handler,
            auth | auth.login_required | Map(
                match('/', 'index') | user
            )
        )

        rctx = app(RequestContext.blank('/login', login='user name', password='12345'))
        r = RequestContext.blank('/')
        r.request.headers['Cookie'] = rctx.response.headers['Set-Cookie']
        print rctx.response.headers['Set-Cookie']
        self.assertEqual(app(r).response.status_int, 200)
