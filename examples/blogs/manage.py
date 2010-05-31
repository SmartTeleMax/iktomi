#!./venv/bin/python

from insanities.ext import sqla
from insanities.management import commands, manage

import cfg
import models
from app import app


if __name__ == '__main__':
    manage(dict(
        # sqlalchemy session
        sqla=sqla.SqlAlchemyCommands(cfg.DATABASES, models.ModelBase),
        # dev-server
        server=commands.server(app),
    ))
