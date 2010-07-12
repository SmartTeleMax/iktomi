#!./venv/bin/python

from os import path
import sys

from mage import manage
from insanities.cmd import server
from insanities.ext import sqla
from insanities.utils import i18n

import cfg
import models
from app import app
from initial import initial

def run(app):
    manage(dict(
        # sqlalchemy session
        sqla=sqla.SqlAlchemyCommands(cfg.DATABASES, models.ModelBase, initial=initial),
        # internationalization
        gettext=i18n.gettext_commands(localedir=cfg.LOCALEDIR,
                                      searchdir=cfg.cur_dir,
                                      modir=cfg.MODIR,
                                      pofiles=cfg.POFILES,
                                      ignore=['*/venv/*']),
        # command to make insanities messages
        ins_gettext=i18n.gettext_commands(localedir=path.join(cfg.insanities_dir, 'locale'),
                                          searchdir=cfg.insanities_dir,
                                          ignore=['*/venv/*'],
                                          domain="insanities-core"),
        # dev-server
        server=server(app),

    ), sys.argv)

if __name__ == '__main__':
    run(app)
