# -*- coding: utf-8 -*-

import unittest
from insanities.web import *
from insanities.web.core import HttpException
from insanities.web.filters import *
from insanities.web.http import RequestContext
from insanities.ext.cache import local_cache_env
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

        app = local_cache_env() | jinja_env() | Map(
            auth.login_handler | login,
            auth.logout_handler | logout,
            auth | Map(
                match('/', 'index')
            )
        )
        rctx = RequestContext.blank('/login', login='user name', password='12345')
        self.assertRaises(HttpException, lambda: app(rctx))

        self.assert_(rctx.response.headers.get('Set-Cookie'))

        try:
            app(rctx)
        except HttpException, e:
            self.assertEqual(e.status, 303)

        r = RequestContext.blank('/logout', login='user name')
        r.request.headers['Cookie'] = rctx.response.headers['Set-Cookie']
        self.assertRaises(HttpException, lambda: app(r))
        try:
            app(r)
        except HttpException, e:
            self.assertEqual(e.status, 303)

    def test_anonym_unauth(self):
        'Anonym and unathorized access'

        def anonym(r):
            self.assert_(r.vals.user is None)

        auth = CookieAuth(user_by_credential, user_by_id)
        app = local_cache_env() | jinja_env() | Map(
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

        app = local_cache_env() | jinja_env() | Map(
            auth.login_handler,
            auth.logout_handler,
            auth | auth.login_required | Map(
                match('/', 'index') | view
            )
        )
        rctx = RequestContext.blank('/')
        self.assertRaises(HttpException, lambda: app(rctx))
        try:
            app(rctx)
        except HttpException, e:
            self.assertEqual(str(e.url), '/login?next=/')

    def test_auth(self):
        'Authorized access'
        auth = CookieAuth(user_by_credential, user_by_id)
        def user(r):
            self.assertEqual(r.vals.user.name, 'user name')
        app = local_cache_env() | jinja_env() | Map(
            auth.login_handler,
            auth.logout_handler,
            auth | auth.login_required | Map(
                match('/', 'index') | user
            )
        )

        try:
            rctx = RequestContext.blank('/login', login='user name', password='12345')
            app(rctx)
        except HttpException:
            pass
        r = RequestContext.blank('/')
        r.request.headers['Cookie'] = rctx.response.headers['Set-Cookie']
        self.assertEqual(app(r).response.status_int, 200)
