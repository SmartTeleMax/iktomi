#!./venv/bin/python

from os import path
import sys

from mage import manage, sqla, fcgi
from mage.app import application

import cfg
import models
from app import app
from initial import initial

def run(app):
    manage(dict(
        # sqlalchemy session
        sqla=sqla.Commands(cfg.DATABASES, models.ModelBase),
        # dev-server
        app=application(app.as_wsgi()),
        # FCGI server
        fcgi=fcgi.Flup(app.as_wsgi()),
    ), sys.argv)

if __name__ == '__main__':
    run(app)
