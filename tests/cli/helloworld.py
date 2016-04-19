from iktomi import web
from iktomi.cli import app
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

app = app.App(webapp, bootstrap=bootstrap)

if __name__=='__main__':
    app.command_serve(port='11111')
