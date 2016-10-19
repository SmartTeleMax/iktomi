# -*- coding: utf-8 -*-
import unittest
import logging
from iktomi import web
from iktomi.auth import CookieAuth, SqlaModelAuth, auth_required, encrypt_password
from iktomi.utils import cached_property
from iktomi.storage import LocalMemStorage

__all__ = ['CookieAuthTests', 'SqlaModelAuthTests']

try:
    from unittest import mock
except ImportError:
    import mock


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
        auth = self.auth = CookieAuth(get_user_identity, identify_user,
                                      expire_time = 7 * 24 * 3600)
        def anonymouse(env, data):
            self.assertTrue(hasattr(env, 'user'))
            self.assertEqual(env.user, None)
            return web.Response('ok')
        def no_anonymouse(env, data):
            self.assertTrue(hasattr(env, 'user'))
            self.assertEqual(env.user, MockUser(name='user name'))
            return web.Response('ok')
        self.app = web.cases(
            auth.login(),
            auth.logout(redirect_to=None),
            auth | web.cases(
                web.match('/a', 'a') | anonymouse,
                web.match('/b', 'b') | auth_required | no_anonymouse,
            ),
        )

    def login(self, login, password):
        return web.ask(self.app, '/login',
                       data={'login':login, 'password':password})

    def test_anonymouse(self):
        '`Auth` anonymouse access'
        response = web.ask(self.app, '/a')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body, b'ok')

        response = web.ask(self.app, '/b')
        self.assertEqual(response.status_int, 303)
        self.assertEqual(response.headers['Location'], '/login?next=/b')

    def test_login(self):
        '`Auth` login of valid user'
        response = self.login('user name', '123')
        self.assertEqual(response.status_int, 303)
        self.assertEqual(response.headers['Location'], '/')
        self.assertTrue('Set-Cookie' in response.headers)

    def test_protected_resource(self):
        '`Auth` requesting protected resource by logined user'
        response = self.login('user name', '123')
        response = web.ask(self.app, '/b',
                           headers={'Cookie': response.headers['Set-Cookie']})
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body, b'ok')

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
        self.assertTrue(response.headers['Set-Cookie']\
                        .startswith('auth=; Max-Age=0; Path=/;'))

    def test_logout_referer(self):
        '`Auth` logout of logined user'
        response = self.login('user name', '123')
        response = web.ask(self.app, '/logout', data={},
                           headers={'Cookie': response.headers['Set-Cookie'],
                                    'Referer': '/somepage'})
        self.assertEqual(response.status_int, 303)
        self.assertEqual(response.headers['Location'], '/somepage')
        self.assertTrue(response.headers['Set-Cookie']\
                        .startswith('auth=; Max-Age=0; Path=/;'))

    def test_expiring_auth(self):
        set_call_args = []
        def set_mock(key, value, time):
            set_call_args.append((key, value, time))
            return True

        with mock.patch('iktomi.storage.LocalMemStorage.set',
                        side_effect=set_mock):
            response = self.login('user name', '123')
            self.assertEqual(response.status_int, 303)
            self.assertEqual(response.headers['Location'], '/')
            self.assertTrue('Set-Cookie' in response.headers)
            # checking set was called with right arguments
            self.assertEqual(len(set_call_args), 1, msg="set was not called")
            auth_cookie = response.headers['Set-Cookie'].split(";")[0]
            key, value, time = set_call_args[0]
            self.assertEqual(key, auth_cookie.replace("=", ":"))
            self.assertEqual(time, 7 * 24 * 3600)
            # calling protected resource to ensure that expire was also called
            # on get request
            with mock.patch('iktomi.storage.LocalMemStorage.get',
                            return_value=value):
                web.ask(self.app, '/b',
                        headers={'Cookie': response.headers['Set-Cookie']})
            # checking set was expire time was renewed with same arguments
            self.assertEqual(len(set_call_args), 2, msg="set was not called")
            key2, value2, time2 = set_call_args[1]
            self.assertEqual(key2, key)
            self.assertEqual(value2, value)
            self.assertEqual(time2, time)

class CookieAuthTestsOnStorageDown(unittest.TestCase):

    def setUp(self):
        class Storage(object):
            def set(self, *args, **kwargs):
                return False
            def delete(self, *args, **kwargs):
                return False

        auth = self.auth = CookieAuth(get_user_identity, identify_user,
                                      storage=Storage())
        def anonymouse(env, data):
            self.assertTrue(hasattr(env, 'user'))
            self.assertEqual(env.user, None)
            return web.Response('ok')
        def no_anonymouse(env, data):
            self.assertTrue(hasattr(env, 'user'))
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
        return web.ask(self.app, '/login',
                       data={'login':login, 'password':password})

    def test_login(self):
        '`Auth` login of valid user'
        warnings = []
        with mock.patch('logging.Logger.warning',
                        side_effect=lambda m, *args:warnings.append(m % args)):
            with self.assertRaises(Exception) as exc:
                self.login('user name', '123')
        self.assertIn('Storage', str(exc.exception))
        self.assertIn('is gone or down', str(exc.exception))
        self.assertEqual(len(warnings), 1)
        self.assertIn('storage', warnings[0])
        self.assertIn('is unreachable', warnings[0])

    def test_anonymouse(self):
        '`Auth` anonymouse access'
        response = web.ask(self.app, '/a')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body, b'ok')

        response = web.ask(self.app, '/b')
        self.assertEqual(response.status_int, 303)
        self.assertEqual(response.headers['Location'], '/login?next=/b')

    def test_logout(self):
        '`Auth` logout of logined user'
        self.auth.crash_without_storage = False

        warnings = []
        response = self.login('user name', '123')
        with mock.patch('logging.Logger.warning',
                        side_effect=lambda m, *args:warnings.append(m % args)):
            response = web.ask(self.app, '/logout', data={},
                               headers={'Cookie': response.headers['Set-Cookie']})
        self.assertEqual(response.status_int, 303)
        self.assertEqual(response.headers['Location'], '/')
        self.assertTrue(response.headers['Set-Cookie']\
                        .startswith('auth=; Max-Age=0; Path=/;'))
        self.assertEqual(len(warnings), 1)
        self.assertIn('storage', warnings[0])
        self.assertIn('is unreachable', warnings[0])


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
            self.assertTrue(hasattr(env, 'user'))
            self.assertEqual(env.user, None)
            return web.Response('ok')

        def no_anonymouse(env, data):
            self.assertTrue(hasattr(env, 'user'))
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
        return web.ask(self.app, '/login',
                       data={'login':login, 'password':password})

    def test_login(self):
        '`SqlaModelAuth` login of valid user'
        response = self.login('user name', '123')
        self.assertEqual(response.status_int, 303)
        self.assertEqual(response.headers['Location'], '/')
        self.assertTrue('Set-Cookie' in response.headers)

        cookie = response.headers['Set-Cookie']
        response = web.ask(self.app, '/b', headers={'Cookie': cookie})
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body, b'ok')

        response = web.ask(self.app, '/logout', data={},
                           headers={'Cookie': cookie})
        self.assertEqual(response.status_int, 303)
        self.assertEqual(response.headers['Location'], '/')
        self.assertTrue(response.headers['Set-Cookie']\
                        .startswith('auth=; Max-Age=0; Path=/;'))

    def test_login_fail_wrong_pass(self):
        '`SqlaModelAuth` login fail: wrong pass'
        response = self.login('user name', '12')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body, b'please login')

    def test_login_fail_no_user(self):
        '`SqlaModelAuth` login fail: no user registered'
        response = self.login('user', '12')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body, b'please login')
