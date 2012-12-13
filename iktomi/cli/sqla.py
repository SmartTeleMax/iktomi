# -*- coding: utf-8 -*-

import sys
from .base import Cli

__all__ = ['Sqla']


class Sqla(Cli):

    def __init__(self, session_maker, initial=None, generators=None):
        self.session = session_maker()
        self.initial = initial
        self.generators = generators or {}

    def _get_binds(self):
        metadatas = {}
        for table, engine in self.session._Session__binds.items():
            metadatas.setdefault(table.metadata, set()).add(engine)
        return metadatas

    def _schema(self, table):
        from sqlalchemy.schema import CreateTable
        return str(CreateTable(table))

    def command_create_tables(self):
        print('Creating table(s)...')
        for metadata, engines in self._get_binds().items():
            for engine in engines:
                for table in metadata.sorted_tables:
                    print('{0}: {1}\n{2}'.format(engine, table.name, self._schema(table)))
                    metadata.create_all(engine, tables=[table])

    def command_drop_tables(self):
        #sys.exit('You must not drop on production server!')
        answer = raw_input('All data will lost. Are you sure? [y/N] ')
        if answer.strip().lower()!='y':
            sys.exit('Interrupted')
        print('Droping table(s)...')
        for metadata, engines in self._get_binds().items():
            for engine in engines:
                metadata.drop_all(engine)

    def command_init(self):
        if self.initial:
            self.initial(self.session)

    def command_reset(self):
        self.command_drop_tables()
        self.command_create_tables()
        self.command_init()

    def command_schema(self, model_name=None):
        for table, engine in self.session._Session__binds.items():
            if model_name:
                if model_name == table.name:
                    print(self._schema(table))
            else:
                print(self._schema(table))

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
