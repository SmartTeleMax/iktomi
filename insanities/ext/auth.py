# -*- coding: utf-8 -*-

import os
import hashlib
import logging
logger = logging.getLogger(__name__)


from ..web.core import STOP, Wrapper, RequestHandler, FunctionWrapper
from ..web.http import HttpException
from ..web.filters import *
from ..utils.i18n import N_
from ..forms import *


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
        Field('login', conv=convs.Char(min_length=3),
              widget=widgets.TextInput(),
              label=N_('Username')),
        Field('password',
              conv=convs.Char(min_length=3),
              widget=widgets.PasswordInput(),
              label=N_(u'Password')),
    )




class CookieAuth(Wrapper):
    '''
    CookieAuth instances allows to add cookies based authentication to you web app.
    It tries to be very agile.
    '''

    #TODO: add "maxage" and "path" parametrs.
    #TODO: add "user_param_name" parametr.
    def __init__(self, user_by_credential, user_by_id, login_url='login', 
                 logout_url='logout', cookie_name='auth', login_form=LoginForm):
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
        super(CookieAuth, self).__init__()
        self._user_by_credential = user_by_credential
        self._user_by_id = user_by_id
        self._login = login_url
        self._logout = logout_url
        self._cookie_name = cookie_name
        self._login_form = login_form

    def handle(self, rctx):
        user = None
        if self._cookie_name in rctx.request.cookies:
            key = rctx.request.cookies[self._cookie_name]
            value = rctx.vals.session_storage.get(key.encode('utf-8'))
            if value is not None:
                user = self._user_by_id(rctx, int(value))
        logger.debug('Got user: %r' % user)
        rctx.vals['user'] = user
        try:
            result = self.exec_wrapped(rctx)
        finally:
            del rctx.vals['user']
        return result

    @property
    def login_handler(self):
        '''
        This property will return component which will handle login requests.
        It is good idea to append some template rendering handler after this component
        to see `login_form`.

            auth.logout_handler | render_to('login.html')
        '''
        def login(rctx):
            form = self._login_form(rctx.vals.form_env)
            if rctx.request.method == 'POST':
                if form.accept(rctx.request.POST):
                    user_id = self._user_by_credential(rctx, **form.python_data)
                    if user_id is not None:
                        key = os.urandom(10).encode('hex')
                        rctx.response.set_cookie(self._cookie_name, key, path='/')
                        if rctx.vals.session_storage.set(key.encode('utf-8'), str(user_id)):
                            pass
                        else:
                            logger.info('session_storage "%r" is unrichable' % rctx.vals.session_storage)
                        next = rctx.request.GET.get('next', '/')
                        raise HttpException(303, url=next)
            return dict(form=form)
        return match('/%s' % self._login, self._login) | login

    @property
    def logout_handler(self):
        '''
        This property will return component which will handle logout requests.
        It only handles POST requests and do not display any rendered content.
        This handler deletes session id from `session_storage`. If there is no
        session id provided or id is incorrect handler silently redirects to login
        url and does not throw any exception.
        '''
        def logout(rctx):
            if self._cookie_name in rctx.request.cookies:
                key = rctx.request.cookies[self._cookie_name]
                if key is not None:
                    rctx.vals.session_storage.delete(key.encode('utf-8'))
                raise HttpException(303, url=rctx.vals.url_for(self._login))
            raise HttpException(404)
        return match('/%s' % self._logout, self._logout) | logout

    @property
    def login_required(self):
        def _login_required(rctx):
            if 'user' in rctx.vals and rctx.vals.user is not None:
                return rctx
            raise HttpException(303, 
                                url=rctx.vals.url_for(self._login).set(next=rctx.request.path))
        return FunctionWrapper(_login_required)
