# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger(__name__)

from werkzeug.contrib.sessions import SessionStore, Session, dump_cookie
from cPickle import dumps, loads, HIGHEST_PROTOCOL

from insanities.web import Wrapper

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


class CookieStore(Wrapper):

    def __init__(self, store, cookie_name='session_id', **kwargs):
        super(CookieStore, self).__init__()

        self.store = store
        self.cookie_name = cookie_name

        self.cookie_args = kwargs
        self.cookie_args.setdefault('max_age', 36000)

        super(CookieStore, self).__init__()

    def handle(self, rctx):
        if self.cookie_name in rctx.request.cookies:
            sid = rctx.request.cookies[self.cookie_name]
            cookie_store = self.store.get(sid)
        else:
            cookie_store = self.store.new()
        rctx.cookie_store = cookie_store

        try:
            rctx = self.exec_wrapped(rctx)
        finally:
            if rctx.cookie_store.should_save:
                self.store.save(rctx.cookie_store)
    
                rctx.response.set_cookie(self.cookie_name,
                                         rctx.cookie_store.sid,
                                         **self.cookie_args)
                logger.debug('Cookie storage: ' + unicode(rctx.cookie_store))
        return rctx


class RCtxFlashMixin(object):

    def has_flash_messages(self):
        return '_flash' in self.cookie_store and \
               len(self.cookie_store['_flash'])

    def get_flash_messages(self):
        if self.has_flash_messages():
            messages = self.cookie_store['_flash']
            del self.cookie_store['_flash']
            return messages
        return []

    def flash(self, message, category=None):
        if '_flash' not in self.cookie_store:
            self.cookie_store['_flash'] = []
        self.cookie_store['_flash'].append((message, category))


