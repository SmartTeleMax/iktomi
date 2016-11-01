# -*- coding: utf-8 -*-

import os
import hashlib
import logging
import binascii
from webob.exc import HTTPSeeOther

logger = logging.getLogger(__name__)


from iktomi import web
from iktomi.forms import *
from iktomi.utils.i18n import N_
from iktomi.storage import LocalMemStorage


def encrypt_password(raw_password, algorithm='sha1', salt=None):
    """
    Returns a string of the hexdigest of the given plaintext password and salt
    using the given algorithm ('md5', 'sha1' or other supported by hashlib).
    """
    if salt is None:
        salt = binascii.hexlify(os.urandom(3))[:5]
    else:
        salt = salt.encode('utf-8')

    raw_password = raw_password.encode('utf-8')
    hash = hashlib.new(algorithm, salt+raw_password).hexdigest()
    return '{}${}${}'.format(algorithm, salt.decode('utf-8'), hash)


def check_password(raw_password, enc_password):
    """
    Returns a boolean of whether the raw_password was correct. Handles
    encryption formats behind the scenes.
    """
    algo, salt, hsh = enc_password.split('$')
    return enc_password == encrypt_password(raw_password, algorithm=algo,
                                            salt=salt)


class LoginForm(Form):
    fields = (
        Field('login', convs.Char(),
              label=N_('Username')),
        Field('password', convs.Char(),
              widget=widgets.PasswordInput(),
              label=N_(u'Password')))


class CookieAuth(web.WebHandler):

    def __init__(self, get_user_identity, identify_user, storage=None,
                 cookie_name='auth', login_form=LoginForm,
                 crash_without_storage=True, expire_time=0):
        self.get_user_identity = get_user_identity
        self.identify_user = identify_user
        self._cookie_name = cookie_name
        self._login_form = login_form
        self.storage = LocalMemStorage() if storage is None else storage
        self.crash_without_storage = crash_without_storage
        self.expire_time = expire_time

    def cookie_auth(self, env, data):
        user = None
        if self._cookie_name in env.request.cookies:
            key = env.request.cookies[self._cookie_name]
            storage_key = self._cookie_name + ':' + key
            user_identity = self.storage.get(storage_key)
            if user_identity is not None:
                user = self.identify_user(env, user_identity)
                self.storage.set(storage_key, user_identity, self.expire_time)
        logger.debug('Authenticated: %r', user)
        env.user = user
        try:
            result = self.next_handler(env, data)
        finally:
            del env.user
        return result
    __call__ = cookie_auth

    def login_identity(self, user_identity, response=None, path='/'):
        key = binascii.hexlify(os.urandom(10)).decode('ascii')
        response = web.Response() if response is None else response
        response.set_cookie(self._cookie_name, key, path=path)
        storage_key = self._cookie_name+':'+key
        if not self.storage.set(storage_key, str(user_identity),
                                self.expire_time):
            logger.warning('storage "%r" is unreachable', self.storage)
            if self.crash_without_storage:
                raise Exception(
                        'Storage {!r} is gone or down'.format(self.storage))
        return response

    def logout_user(self, request, response):
        if self._cookie_name in request.cookies:
            response.delete_cookie(self._cookie_name)
            key = request.cookies[self._cookie_name]
            if key is not None:
                if not self.storage.delete(self._cookie_name + ':' + key):
                    logger.warning('storage "%r" is unreachable', self.storage)

    def login(self, template='login'):
        '''
        This property will return component which will handle login requests.

            auth.login(template='login.html')
        '''
        def _login(env, data):
            form = self._login_form(env)
            next = env.request.GET.get('next', '/')
            login_failed = False
            if env.request.method == 'POST':
                if form.accept(env.request.POST):
                    user_identity = self.get_user_identity(
                                                env, **form.python_data)
                    if user_identity is not None:
                        response = HTTPSeeOther(location=next)
                        return self.login_identity(user_identity, response)
                    login_failed = True
            data.form = form
            data.login_failed = login_failed
            data.login_url = env.root.login.as_url.qs_set(next=next)
            return env.template.render_to_response(template, data.as_dict())
        return web.match('/login', 'login') | _login

    def logout(self, redirect_to='/'):
        '''
        This property will return component which will handle logout requests.
        It only handles POST requests and do not display any rendered content.
        This handler deletes session id from `storage`. If there is no
        session id provided or id is incorrect handler silently redirects to
        login url and does not throw any exception.
        '''
        def _logout(env, data):
            location = redirect_to
            if location is None and env.request.referer:
                location = env.request.referer
            elif location is None:
                location = '/'
            response = HTTPSeeOther(location=str(location))
            self.logout_user(env.request, response)
            return response
        return web.match('/logout', 'logout') | web.method('post') | _logout


@web.request_filter
def auth_required(env, data, next_handler):
    if getattr(env, 'user', None) is not None:
        return next_handler(env, data)
    response = web.Response(status=303)
    response.headers['Location'] = str(
                env.root.login.as_url.qs_set(next=env.request.path_info))
    return response


class SqlaModelAuth(CookieAuth):

    def __init__(self, model, storage=None, login_field='login',
                 password_field='password', **kwargs):
        self._model = model
        self._login_field = login_field
        self._password_field = password_field
        CookieAuth.__init__(self, self.get_user_identity, self.identify_user,
                            storage=storage, **kwargs)

    def get_query(self, env, login):
        model = self._model
        login_field = getattr(model, self._login_field)
        return env.db.query(model).filter(login_field==login)

    def get_user_identity(self, env, login, password):
        user = self.get_query(env, login).first()
        if user is not None:
            stored_password = getattr(user, self._password_field)
            if check_password(password, stored_password):
                return user.id
        return None

    def identify_user(self, env, user_identity):
        return env.db.query(self._model).get(user_identity)
