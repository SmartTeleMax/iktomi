#!./venv/bin/python

from os import path

from insanities.ext import sqla, gettext
from insanities.management import commands, manage

import cfg
import models
from app import app
from initial import initial

def run(app):
    manage(dict(
        # sqlalchemy session
        sqla=sqla.SqlAlchemyCommands(cfg.DATABASES, models.ModelBase, initial=initial),
        # internationalization
        gettext=gettext.gettext_commands(localedir=cfg.LOCALEDIR,
                                         searchdir=cfg.cur_dir,
                                         modir=cfg.MODIR,
                                         pofiles=cfg.POFILES,
                                         ignore=['*/venv/*']),
        # command to make insanities messages
        insanities_gettext=gettext.gettext_commands(
                                         localedir=path.join(cfg.insanities_dir, 'locale'),
                                         searchdir=cfg.insanities_dir,
                                         ignore=['*/venv/*'],
                                         domain="insanities-core"),
        # dev-server
        server=commands.server(app),

    ))

if __name__ == '__main__':
    run(app)
