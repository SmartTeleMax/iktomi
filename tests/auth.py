# -*- coding: utf-8 -*-

import unittest
from iktomi import web
from iktomi.auth import CookieAuth, SqlaModelAuth, auth_required, encrypt_password
from iktomi.utils import cached_property

__all__ = ['CookieAuthTests', 'SqlaModelAuthTests']


class MockUser(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)
    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.name == self.name


class MockTemplateManager(object):
    templates = {
        'login': 'please login',
    }
    def render_to_response(self, template, data):
        return web.Response(self.templates[template])



def get_user_identity(env, login, password):
    if password == '123':
        return 'user-identity'


def identify_user(env, user_identity):
    return MockUser(name='user name')


class CookieAuthTests(unittest.TestCase):
    def setUp(self):
        auth = self.auth = CookieAuth(get_user_identity, identify_user)
        def anonymouse(env, data):
            self.assert_(hasattr(env, 'user'))
            self.assertEqual(env.user, None)
            return web.Response('ok')
        def no_anonymouse(env, data):
            self.assert_(hasattr(env, 'user'))
            self.assertEqual(env.user, MockUser(name='user name'))
            return web.Response('ok')
        self.app = web.cases(
            auth.login(),
            auth.logout(),
            auth | web.cases(
                web.match('/a', 'a') | anonymouse,
                web.match('/b', 'b') | auth_required | no_anonymouse,
            ),
        )

    def login(self, login, password):
        return web.ask(self.app, '/login', data={'login':login, 'password':password})

    def test_anonymouse(self):
        '`Auth` anonymouse access'
        response = web.ask(self.app, '/a')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body, 'ok')

        response = web.ask(self.app, '/b')
        self.assertEqual(response.status_int, 303)
        self.assertEqual(response.headers['Location'], '/login?next=/b')

    def test_login(self):
        '`Auth` login of valid user'
        response = self.login('user name', '123')
        self.assertEqual(response.status_int, 303)
        self.assertEqual(response.headers['Location'], '/')
        self.assert_('Set-Cookie' in response.headers)

    def test_protected_resource(self):
        '`Auth` requesting protected resource by logined user'
        response = self.login('user name', '123')
        response = web.ask(self.app, '/b', headers={'Cookie': response.headers['Set-Cookie']})
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body, 'ok')

    def test_logout_anonymouse(self):
        '`Auth` logout of anonymouse'
        response = web.ask(self.app, '/logout', data={})
        self.assertEqual(response.status_int, 303)

    def test_logout_by_get(self):
        '`Auth` logout by GET metod'
        response = web.ask(self.app, '/logout')
        self.assertEqual(response, None)

    def test_logout(self):
        '`Auth` logout of logined user'
        response = self.login('user name', '123')
        response = web.ask(self.app, '/logout', data={},
                           headers={'Cookie': response.headers['Set-Cookie']})
        self.assertEqual(response.status_int, 303)
        self.assertEqual(response.headers['Location'], '/')
        self.assert_(response.headers['Set-Cookie'].startswith('auth=; Max-Age=0; Path=/;'))


class CookieAuthTestsOnStorageDown(unittest.TestCase):
    def setUp(self):
        class Storage(object):
            def set(self, *args, **kwargs):
                return False

        auth = self.auth = CookieAuth(get_user_identity, identify_user,
                                      storage=Storage())
        def anonymouse(env, data):
            self.assert_(hasattr(env, 'user'))
            self.assertEqual(env.user, None)
            return web.Response('ok')
        def no_anonymouse(env, data):
            self.assert_(hasattr(env, 'user'))
            self.assertEqual(env.user, MockUser(name='user name'))
            return web.Response('ok')
        self.app = web.cases(
            auth.login(),
            auth.logout(),
            auth | web.cases(
                web.match('/a', 'a') | anonymouse,
                web.match('/b', 'b') | auth_required | no_anonymouse,
            ),
        )

    def login(self, login, password):
        return web.ask(self.app, '/login', data={'login':login, 'password':password})

    def test_login(self):
        '`Auth` login of valid user'
        with self.assertRaises(Exception):
            self.login('user name', '123')

    def test_anonymouse(self):
        '`Auth` anonymouse access'
        response = web.ask(self.app, '/a')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body, 'ok')

        response = web.ask(self.app, '/b')
        self.assertEqual(response.status_int, 303)
        self.assertEqual(response.headers['Location'], '/login?next=/b')


class SqlaModelAuthTests(unittest.TestCase):

    def setUp(self):
        from sqlalchemy import Column, Integer, String, create_engine, orm
        from sqlalchemy.schema import MetaData
        from sqlalchemy.ext.declarative import declarative_base
        metadata = MetaData()
        Model = declarative_base(metadata=metadata)
        class User(Model):
            __tablename__ = 'users'
            id = Column(Integer, primary_key=True)
            login = Column(String(255), nullable=False, unique=True)
            password = Column(String(255), nullable=False)
        auth = SqlaModelAuth(User)

        class Env(web.AppEnvironment):

            @cached_property
            def db(self):
                return orm.sessionmaker(bind=create_engine('sqlite://'))()

            @cached_property
            def template(self):
                return MockTemplateManager()

        @web.request_filter
        def make_env(env, data, nxt):
            metadata.create_all(env.db.bind)
            user = User(login='user name', password=encrypt_password('123'))
            env.db.add(user)
            env.db.commit()
            try:
                return nxt(env, data)
            finally:
                env.db.close()

        def anonymouse(env, data):
            self.assert_(hasattr(env, 'user'))
            self.assertEqual(env.user, None)
            return web.Response('ok')

        def no_anonymouse(env, data):
            self.assert_(hasattr(env, 'user'))
            self.assertEqual(env.user.login, 'user name')
            return web.Response('ok')

        app = make_env | web.cases(
            auth.login(),
            auth.logout(),
            auth | web.cases(
                web.match('/a', 'a') | anonymouse,
                web.match('/b', 'b') | auth_required | no_anonymouse,
            ),
        )
        self.app = web.Application(app, Env)

    def login(self, login, password):
        return web.ask(self.app, '/login', data={'login':login, 'password':password})

    def test_login(self):
        '`SqlaModelAuth` login of valid user'
        response = self.login('user name', '123')
        self.assertEqual(response.status_int, 303)
        self.assertEqual(response.headers['Location'], '/')
        self.assert_('Set-Cookie' in response.headers)

        cookie = response.headers['Set-Cookie']
        response = web.ask(self.app, '/b', headers={'Cookie': cookie})
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body, 'ok')

        response = web.ask(self.app, '/logout', data={}, headers={'Cookie': cookie})
        self.assertEqual(response.status_int, 303)
        self.assertEqual(response.headers['Location'], '/')
        self.assert_(response.headers['Set-Cookie'].startswith('auth=; Max-Age=0; Path=/;'))

    def test_login_fail_wrong_pass(self):
        '`SqlaModelAuth` login fail: wrong pass'
        response = self.login('user name', '12')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body, 'please login')

    def test_login_fail_no_user(self):
        '`SqlaModelAuth` login fail: no user registered'
        response = self.login('user', '12')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body, 'please login')
