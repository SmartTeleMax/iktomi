#!./venv/bin/python

from os import path
import sys

from mage import manage
from insanities.cmd import server
from insanities.web.wsgi import WSGIHandler

import cfg
from app import app

def run(app):
    manage(dict(
        # dev-server
        server=server(WSGIHandler(app)),
    ), sys.argv)

if __name__ == '__main__':
    run(app)
