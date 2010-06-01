# -*- coding: utf-8 -*-

__all__ = ['WSGIHandler']

import logging
import httplib
from .http import HttpException, RequestContext
from .core import ContinueRoute

logger = logging.getLogger(__name__)


class WSGIHandler(object):

    def __init__(self, app):
        self.app = app

    def status(self, number):
        return '%d %s' % (number, httplib.responses[number])

    def __call__(self, env, start_response):
        rctx = RequestContext(env)
        try:
            rctx = self.app(rctx)
        except ContinueRoute, e:
            pass
        headers = rctx.response.headers.items()
        start_response(rctx.response.status, headers)
        return [rctx.response.body]
