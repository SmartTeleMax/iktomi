# -*- coding: utf-8 -*-

import os
import hashlib
import logging
logger = logging.getLogger(__name__)


from insanities import web
from insanities.forms import *
from insanities.utils import N_


def encrypt_password(raw_password, algorithm='sha1', salt=None):
    """
    Returns a string of the hexdigest of the given plaintext password and salt
    using the given algorithm ('md5', 'sha1' or other supported by hashlib).
    """
    if salt is None:
        salt = os.urandom(3).encode('hex')[:5]
    raw_password = raw_password.encode('utf-8')
    salt = salt.encode('utf-8')
    hash = hashlib.new(algorithm, salt+raw_password).hexdigest()
    return '%s$%s$%s' % (algorithm, salt, hash)


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

    def __init__(self, get_user_identity, identify_user, session_storage,
                 cookie_name='auth', login_form=LoginForm):
        self.get_user_identity = get_user_identity
        self.identify_user = identify_user
        self._cookie_name = cookie_name
        self._login_form = login_form
        self.session_storage = session_storage

    def handle(self, env, data, next_handler):
        user = None
        if self._cookie_name in env.request.cookies:
            key = env.request.cookies[self._cookie_name]
            user_identity = self.session_storage.get(self._cookie_name+':'+key.encode('utf-8'))
            if user_identity is not None:
                user = self.identify_user(env, user_identity)
        logger.debug('Authenticated: %r' % user)
        env.user = user
        try:
            result = next_handler(env, data)
        finally:
            del env.user
        return result

    def login_identity(self, user_identity, response=None, path='/'):
        key = os.urandom(10).encode('hex')
        response = web.Response() if response is None else response
        response.set_cookie(self._cookie_name, key, path=path)
        if not self.session_storage.set(self._cookie_name+':'+key.encode('utf-8'), 
                                        str(user_identity)):
            logger.info('session_storage "%r" is unrichable' % self.session_storage)
        return response

    def logout_user(self, request):
        response = web.Response()
        response.delete_cookie(self._cookie_name)
        key = request.cookies[self._cookie_name]
        if key is not None:
            if not self.session_storage.delete(self._cookie_name+':'+key.encode('utf-8')):
                logger.info('session_storage "%r" is unrichable' % self.session_storage)
        return response

    def login(self, template='login'):
        '''
        This property will return component which will handle login requests.
        It is good idea to append some template rendering handler after this component
        to see `login_form`.

            auth.login(template='login.html')
        '''
        def _login(env, data, next_handler):
            form = self._login_form(env)
            next = env.request.GET.get('next', '/')
            msg = ''
            if env.request.method == 'POST':
                if form.accept(env.request.POST):
                    user_identity = self.get_user_identity(env, **form.python_data)
                    if user_identity is not None:
                        response = self.login_identity(user_identity)
                        response.status = 303
                        response.headers['Location'] = next.encode('utf-8')
                        return response
                    msg = 'user or password is wrong'
            data.form = form
            data.message = msg
            data.login_url = env.root.login.as_url.qs_set(next=next)
            return env.template.render_to_response(template, data.as_dict())
        return web.match('/login', 'login') | _login

    def logout(self, redirect_to='/'):
        '''
        This property will return component which will handle logout requests.
        It only handles POST requests and do not display any rendered content.
        This handler deletes session id from `session_storage`. If there is no
        session id provided or id is incorrect handler silently redirects to login
        url and does not throw any exception.
        '''
        def _logout(env, data, next_handler):
            if self._cookie_name in env.request.cookies:
                response = self.logout_user(env.request)
                response.status = 303
                response.headers['Location'] = str(redirect_to)
                return response
            return next_handler(env, data)
        return web.match('/logout', 'logout') | web.method('post') | _logout


@web.handler
def auth_required(env, data, next_handler):
    if 'user' in env and env.user is not None:
        return next_handler(env, data)
    response = web.Response(status=303)
    response.headers['Location'] = str(env.root.login.as_url.qs_set(next=env.request.path_info))
    return response


class SqlaModelAuth(CookieAuth):

    class Mixin(object):
        def set_password(self, password):
            self.password = encrypt_password(password)

        def check_password(self, password):
            return check_password(password, self.password)

        @classmethod
        def login(cls):
            return cls.login

        @classmethod
        def get_user_identity(cls, env, login, password):
            user = env.db.query(cls).filter(cls.login()==login).first()
            if user and check_password(password, user.password):
                return user.id
            return None

        @classmethod
        def identify_user(cls, env, user_identity):
            return env.db.get(cls, id=user_identity)

    def __init__(self, model, session_storage, **kwargs):
        CookieAuth.__init__(self, model.get_user_identity, model.identify_user, session_storage, **kwargs)
