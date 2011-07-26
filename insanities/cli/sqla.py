# -*- coding: utf-8 -*-

import sys
from insanities.utils import import_string
from .base import Cli

__all__ = ['Sqla']


class Sqla(Cli):

    def __init__(self, session_maker, initial=None, generators=None):
        self.session = session_maker()
        self.initial = initial
        self.generators = generators or {}

    def command_create_tables(self):
        print('Creating table(s)...')
        for table, engine in self.session._Session__binds.items():
            print('{1}: {0}'.format(table.name, engine))
            table.metadata.create_all(engine)

    def command_drop_tables(self):
        #sys.exit('You must not drop on production server!')
        answer = raw_input('All data will lost. Are you sure? [y/N] ')
        if answer.strip().lower()!='y':
            sys.exit('Interrupted')
        print('Droping table(s)...')
        for table, engine in self.session._Session__binds.items():
            print('{1}: {0}'.format(table.name, engine))
            table.metadata.drop_all(engine, checkfirst=True)

    def command_init(self):
        if self.initial:
            #TODO: implement per db initial
            self.initial(self.session)

    def command_reset(self):
        self.command_drop_tables()
        self.command_create_tables()
        self.command_init()

    def command_schema(self, model_name=None):
        from sqlalchemy.schema import CreateTable
        for table, engine in self.session._Session__binds.items():
            if model_name:
                if model_name == table.name:
                    print(str(CreateTable(table)))
            else:
                print(str(CreateTable(table)))

    def command_gen(self, *names):
        if not names:
            raise Exception('Please provide generator names')
        for name in names:
            name, count = name, 0
            if ':' in name:
                name, count = name.split(':', 1)
            count = int(count)
            create = self.generators[name]
            print('Generating `{0}` count={1}'.format(name, count))
            create(self.session, count)
            self.session.commit()
