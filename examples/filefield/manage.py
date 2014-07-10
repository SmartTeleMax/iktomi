#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
import sys, logging
from iktomi.cli import manage
from iktomi.cli.app import App
import app
from iktomi.cli.fcgi import Flup

def run(args=sys.argv):
    manage(dict(
        # sqlalchemy session
        server=App(app.wsgi_app),
        flup=Flup(app.wsgi_app, **app.cfg.FLUP_ARGS),
    ), args)


if __name__ == '__main__':
    logging.basicConfig(
            #format='%(asctime)s: %(levelname)-5s: %(name)-15s: %(message)s',
            format='%(name)-15s: %(message)s',
            level=logging.DEBUG)
    logging.getLogger('iktomi.templates').setLevel(logging.WARNING)
    logging.getLogger('iktomi.auth').setLevel(logging.WARNING)
    logging.getLogger('iktomi.web.filters').setLevel(logging.WARNING)
    logging.getLogger('iktomi.web.url_templates').setLevel(logging.WARNING)
    run()
