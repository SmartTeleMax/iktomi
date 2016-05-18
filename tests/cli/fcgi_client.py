# -*- coding: utf-8 -*-
from io import StringIO
from flup.client.fcgi_app import FCGIApp


class FastCGIClient(object):

    def __init__(self, connection, start_response=(lambda s, h: None)):
        self.app = FCGIApp(connect=connection)
        self.start_response = start_response

    def make_request(self, method='GET', path='/', data=None, **kwargs):
        errors = StringIO()
        env = {'HTTP_HOST':'localhost',
               'SERVER_PORT':'80',
               'SERVER_NAME':'localhost',
               'SERVER_PROTOCOL':'HTTP/1.1',
               'wsgi.input':StringIO(data),
               'wsgi.errors':errors}
        env['REQUEST_METHOD'] = method
        env['PATH_INFO'] = path
        for k, v in kwargs.items():
            env[k] = v

        result = self.app(environ=env, start_response=self.start_response)
        return result, errors.getvalue()
