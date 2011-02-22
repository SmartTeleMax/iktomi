# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger(__name__)

from werkzeug.contrib.sessions import SessionStore, Session, dump_cookie
from cPickle import dumps, loads, HIGHEST_PROTOCOL
from werkzeug.exc import HTTPException

raise NotImplementedError('This module is not tested')

__all__ = ['CacheSessionStore', 'CookieStore']



class SessionStoreError(Exception):

    def __str__(self):
        return 'Failed to store session. Is session store configured '\
                'properly and running?'


class CacheSessionStore(SessionStore):

    def __init__(self, cache, session_class=None, timeout=24*60*60):
        self.cache = cache
        self.session_class = session_class or Session
        self.timeout = timeout

    def save(self, session):
        if not self.cache.set(session.sid,
                              dumps(dict(session), HIGHEST_PROTOCOL),
                              time=self.timeout):
            raise SessionStoreError()

    def delete(self, session):
        self.cache.delete(session.sid)

    def get(self, sid):
        data = self.cache.get(sid)
        if not data:
            return self.new()
        return self.session_class(loads(data), sid, False)


def cookie_store(storage, cookie_name='session_id', cookie_args=None):

    cookie_args = cookie_args or {}
    cookie_args.setdefault('max_age', 36000)

    def handle(env, data, next_handler):
        if cookie_name in env.request.cookies:
            sid = env.request.cookies[self.cookie_name]
            env.cookie_store = storage.get(sid)
        else:
            env.cookie_store = storage.new()

        try:
            response = next_handler(env, data)
        except HTTPException, e:
            response = e

        # XXX response == None
        if response and env.cookie_store.should_save:
            storage.save(env.cookie_store)

            response.set_cookie(cookie_name,
                                env.cookie_store.sid,
                                **cookie_args)
        return response
    return handle


class flash_messages(env):

    def has_flash_messages():
        return '_flash' in env.cookie_store and \
               len(env.cookie_store['_flash'])

    def get_flash_messages():
        if env.has_flash_messages():
            messages = env.cookie_store['_flash']
            del env.cookie_store['_flash']
            return messages
        return []

    def flash(message, category=None):
        if '_flash' not in env.cookie_store:
            env.cookie_store['_flash'] = []
        env.cookie_store['_flash'].append((message, category))


