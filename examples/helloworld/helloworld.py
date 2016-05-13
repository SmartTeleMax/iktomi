from iktomi import web
from iktomi.cli import app, fcgi, manage
import os
import sys
import logging

webapp = web.Application(web.cases(
    web.match('/', 'index') | (lambda e, d: web.Response('hello world'))
), web.AppEnvironment)

# adding custom logging config to test bootstrapping
def bootstrap():
    logpath = os.path.join(os.path.dirname(__file__),
                          'hello.log')
    hellolog = logging.FileHandler(logpath)
    logging.root.handlers.append(hellolog)

devapp = app.App(webapp, bootstrap=bootstrap)
fcgi_sock_path = os.path.join(os.path.dirname(__file__), 'fcgi.sock')
fcgi_app = fcgi.Flup(webapp, bind=fcgi_sock_path, cwd=os.path.dirname(__file__))


if __name__=='__main__':
    manage(dict(dev=devapp,
                fcgi=fcgi_app))
