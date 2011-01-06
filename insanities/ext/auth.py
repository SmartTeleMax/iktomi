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
              label=N_(u'Password')))


class CookieAuth(web.WebHandler):
    '''
    CookieAuth instances allows to add cookies based authentication to you web app.
    It tries to be very agile.
    '''

    #TODO: add "maxage" and "path" parametrs.
    #TODO: add "user_param_name" parametr.
    def __init__(self, user_by_credential, user_by_id, session_storage,
                 login_url='login', logout_url='logout', cookie_name='auth',
                 login_form=LoginForm):
        '''
        Each instance of this class handles cookie base authentication.
        You may have multiple instances of `CookieAuth` in single webapp 
        (just use different values for `cookie_name`).

        :*user_by_credential* - callable that gets `rctx` and data from `login_form`.
                                It must return user id or None.

        :*user_by_id* - callable that gets `rctx` and id. It must return User or None.

        :*login_url* - string that will be substitute to `match` filter as value and url name.
                       default value is 'login', so `match('/login', 'login')`

        :*logout_url* - same as `login_url` but for logout.

        :*cookie_name* - name for cookie. If you want multiple instances of this class you'll
                        better specify different `cookie_name` for each instance.

        :*login_form* - class of login form. Data from this form will be passed to `user_by_credential`.
        '''
        self._user_by_credential = user_by_credential
        self._user_by_id = user_by_id
        self._login = login_url
        self._logout = logout_url
        self._cookie_name = cookie_name
        self._login_form = login_form
        self.session_storage = session_storage

    def handle(self, env, data, next_handler):
        user = None
        if self._cookie_name in env.request.cookies:
            key = env.request.cookies[self._cookie_name]
            value = self.session_storage.get(self._cookie_name+':'+key.encode('utf-8'))
            if value is not None:
                user = self._user_by_id(env, int(value))
        logger.debug('Got user: %r' % user)
        env.user = user
        try:
            result = next_handler(env, data)
        finally:
            del env.user
        return result

    def login(self, user_id):
        key = os.urandom(10).encode('hex')
        response = web.Response()
        response.set_cookie(self._cookie_name, key, path='/')
        if not self.session_storage.set(self._cookie_name+':'+key.encode('utf-8'), 
                                        str(user_id)):
            logger.info('session_storage "%r" is unrichable' % self.session_storage)
        return response

    def logout(self, request):
        response = web.Response()
        response.delete_cookie(self._cookie_name)
        key = request.cookies[self._cookie_name]
        if key is not None:
            if not self.session_storage.delete(self._cookie_name+':'+key.encode('utf-8')):
                logger.info('session_storage "%r" is unrichable' % self.session_storage)
        return response

    @property
    def login_handler(self):
        '''
        This property will return component which will handle login requests.
        It is good idea to append some template rendering handler after this component
        to see `login_form`.

            auth.logout_handler | render_to('login.html')
        '''
        def login(env, data, next_handler):
            form = self._login_form(env)
            next = env.request.GET.get('next', '/')
            msg = ''
            if env.request.method == 'POST':
                if form.accept(env.request.POST):
                    user_id, msg = self._user_by_credential(env, **form.python_data)
                    if user_id is not None:
                        response = self.login(user_id)
                        response.status = 303
                        response.headers['Location'] = next
                        return response
            data.form = form
            data.message = msg
            data.login_url = env.url_for(self._login).set(next=next)
            return next_handler(env, data)
        return web.match('/%s' % self._login, self._login) | login

    @property
    def logout_handler(self):
        '''
        This property will return component which will handle logout requests.
        It only handles POST requests and do not display any rendered content.
        This handler deletes session id from `session_storage`. If there is no
        session id provided or id is incorrect handler silently redirects to login
        url and does not throw any exception.
        '''
        def logout(env, data, next_handler):
            if self._cookie_name in env.request.cookies:
                response = self.logout(env.request)
                response.status = 303
                response.headers['Location'] = '/'
                return response
            return next_handler(env, data)
        return web.match('/%s' % self._logout, self._logout) | logout

    @property
    def login_required(self):
        def _login_required(env, data, next_handler):
            if 'user' in env and env.user is not None:
                return next_handler(env, data)
            response = web.Response(status=303)
            response.headers['Location'] = str(env.url_for(self._login).set(next=env.request.path_info))
            return response
        return web.handler(_login_required)

