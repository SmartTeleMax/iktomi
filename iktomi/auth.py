# -*- coding: utf-8 -*-

import os
import hashlib
import logging
from webob.exc import HTTPSeeOther

logger = logging.getLogger(__name__)


from iktomi import web
from iktomi.forms import *
from iktomi.utils import N_
from iktomi.storage import LocalMemStorage


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

    def __init__(self, get_user_identity, identify_user, storage=None,
                 cookie_name='auth', login_form=LoginForm,
                 crash_without_storage=True):
        self.get_user_identity = get_user_identity
        self.identify_user = identify_user
        self._cookie_name = cookie_name
        self._login_form = login_form
        self.storage = LocalMemStorage() if storage is None else storage
        self.crash_without_storage = crash_without_storage

    def cookie_auth(self, env, data):
        user = None
        if self._cookie_name in env.request.cookies:
            key = env.request.cookies[self._cookie_name]
            user_identity = self.storage.get(self._cookie_name + ':' + 
                                                    key.encode('utf-8'))
            if user_identity is not None:
                user = self.identify_user(env, user_identity)
        logger.debug('Authenticated: %r', user)
        env.user = user
        try:
            result = self.next_handler(env, data)
        finally:
            del env.user
        return result
    __call__ = cookie_auth

    def login_identity(self, user_identity, response=None, path='/'):
        key = os.urandom(10).encode('hex')
        response = web.Response() if response is None else response
        response.set_cookie(self._cookie_name, key, path=path)
        if not self.storage.set(self._cookie_name+':'+key.encode('utf-8'),
                                str(user_identity)):
            if self.crash_without_storage:
                raise Exception('Storage `%r` is gone or down' % self.storage)
            logger.info('storage "%r" is unrichable', self.storage)
        return response

    def logout_user(self, request, response):
        if self._cookie_name in request.cookies:
            response.delete_cookie(self._cookie_name)
            key = request.cookies[self._cookie_name]
            if key is not None:
                if not self.storage.delete(self._cookie_name + ':' + \
                                                key.encode('utf-8')):
                    logger.info('storage "%r" is unrichable', self.storage)

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
                        response = self.login_identity(user_identity)
                        response.status = 303
                        response.headers['Location'] = next.encode('utf-8')
                        return response
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
            response = HTTPSeeOther(location=str(redirect_to))
            self.logout_user(env.request, response)
            return response
        return web.match('/logout', 'logout') | web.method('post') | _logout


class SqlaModelAuth(CookieAuth):

    def __init__(self, model, storage=None, login_field='login',
                 password_field='password', **kwargs):
        self._model = model
        self._login_field = login_field
        self._password_field = password_field
        CookieAuth.__init__(self, self.get_user_identity, self.identify_user,
                            storage=storage, **kwargs)

    def get_user_identity(self, env, login, password):
        model = self._model
        login_field = getattr(model, self._login_field)
        user = env.db.query(model).filter(login_field==login).first()
        if user is not None:
            stored_password = getattr(user, self._password_field)
            if check_password(password, stored_password):
                return user.id
        return None

    def identify_user(self, env, user_identity):
        return env.db.query(self._model).get(user_identity)



class DBAuth(object):

    def __init__(self, model, login_form=LoginForm):
        self.model = model
        self.login_form = login_form

    def get_user(self, env):
        sid = env.request.cookies.get('sid')
        if sid:
            user = env.db.get(User, sid=sid)
            if user is None:
                self.set_user(env, None)
            else:
                env.user = user
                logger.debug('Authenticated: %s' % user.id)
        else:
            env.user = None
        return env.user

    def set_user(self, env, user):
        # IMPORTANT: Called responsible to commit after setting user!
        env.user = user
        if user is not None and not user.sid:
            for attempt in range(3):
                sid = os.urandom(10).encode('hex')
                if env.db.get(User, sid=sid) is None:
                    user.sid = sid
                    break
            else:
                raise RuntimeError('Failed to generate unique session ID')

    def set_cookies(self, env, response, remember=False):
        if response is not None:
            if env.user is None:
                response.delete_cookie('sid')
                response.delete_cookie('name')
                response.delete_cookie('url')
            else:
                params = {'max_age': 30*24*3600} if remember else {}
                name = urlquote(env.user.full_name)
                url = env.url_for('users.profile')
                response.set_cookie('sid', env.user.sid, **params)
                response.set_cookie('name', name, **params)
                response.set_cookie('url', url, **params)
        return response

    # ======================== LOGIN =====================

    def login_handler(self, env, data, nxt):
        data.form = form = self.login_form(env)
        if env.request.method == 'POST':
            data.failed = data.submit = True
            #TODO: flood check
            if form.accept(env.request.POST):
                email = form.python_data['email']
                user = env.db.get(User, email=email)
                if user and user.check_password(form.python_data['password']):
                    # sid is storing in db
                    self.set_user(env, user)
                    env.db.commit()
                    data.failed = False
        else:
            data.submit = data.failed = False
        remember = env.request.POST.get('remember')
        return self.set_cookies(env, nxt(env, data), remember=remember)

    def login_render_html(self, env, data):
        if data.failed or not data.submit:
            return env.render_to_response('users/login', {
                'form': data.form,
                'failed': data.failed,
            })
        return env.redirect_to('users.profile')

    def login_render_ajax(self, env, data):
        if data.failed:
            # For ajax request this method call means we have
            # errors in form
            return env.json({
                'status':'FAIL',
                'errors':dict(map(lambda field: (field.name, u'Пользователь не существует'), 
                                  data.form.fields)),
            })
        return env.json({
            'status': 'OK',
            'name': env.user.name,
            'url': env.url_for('users.profile'),
        })

    # ========================== LOGOUT ==============================

    def logout_handler(self, env, data, nxt):
        self.set_user(env, None)
        env.db.commit()
        return self.set_cookies(env, nxt(env, data))

    def logout_render_ajax(self, env, data):
        return env.json({'status':'OK'})

    def logout_render_html(self, env, data):
        return env.redirect_to('users.login')

    # ======================= HANDLERS ==============================
    def required(self):
        def _required(env, data, nxt):
            if env.user is not None:
                return nxt(env, data)
            redirect = env.redirect_to('users.login', {'next': env.request.path_info})
            # in case there are cookies stuck in the request
            return self.set_cookies(env, redirect)
        return web.request_filter(_required)

    def login(self, success=None, show_form=None):
        return web.match('/login', 'login') | \
                web.request_filter(self.login_handler) | \
                self.login_render_html

    def login_ajax(self):
        return web.match('/login/ajax', 'login_ajax') | \
                web.request_filter(self.login_handler) | \
                web.method('post') | \
                self.login_render_ajax


    def logout(self):
        return web.match('/logout', 'logout') | \
                web.method('post') | \
                web.request_filter(self.logout_handler) | \
                self.logout_render_html

    def logout_ajax(self):
        return web.match('/logout/ajax', 'logout_ajax') | \
                web.method('post') | \
                web.request_filter(self.logout_handler) | \
                self.logout_render_ajax
