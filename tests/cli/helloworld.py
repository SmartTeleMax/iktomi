from iktomi import web
from iktomi.cli import app
import os
import sys

webapp = web.Application(web.cases(
    web.match('/', 'index') | (lambda e, d: web.Response('hello world'))
), web.AppEnvironment)

app = app.App(webapp)

if __name__=='__main__':
    app.command_serve(port='11111')
