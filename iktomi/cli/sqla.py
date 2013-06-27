# -*- coding: utf-8 -*-

import sys
from sqlalchemy import create_engine
from sqlalchemy.types import SchemaType
from sqlalchemy.engine import reflection
from sqlalchemy.schema import (
    MetaData,
    Table,
    DropTable,
    ForeignKeyConstraint,
    DropConstraint,
)
from .base import Cli

__all__ = ['Sqla']


def drop_everything(engine):
    '''Droping all tables and custom types (enums) using `engine`.
    Taken from http://www.sqlalchemy.org/trac/wiki/UsageRecipes/DropEverything
    
    This method is more robust than `metadata.drop_all(engine)`. B.c. when
    you change a table or a type name, `drop_all` does not consider the old one.
    Thus, DB holds some unused entities.'''
    conn = engine.connect()
    # the transaction only applies if the DB supports
    # transactional DDL, i.e. Postgresql, MS SQL Server
    trans = conn.begin()
    inspector = reflection.Inspector.from_engine(engine)
    metadata = MetaData()
    tbs = []
    all_fks = []
    types = []
    for table_name in inspector.get_table_names():
        fks = []
        for fk in inspector.get_foreign_keys(table_name):
            if not fk['name']:
                continue
            fks.append(ForeignKeyConstraint((), (), name=fk['name']))
        for col in inspector.get_columns(table_name):
            if isinstance(col['type'], SchemaType):
                types.append(col['type'])
        t = Table(table_name,metadata,*fks)
        tbs.append(t)
        all_fks.extend(fks)
    try:
        for fkc in all_fks:
            conn.execute(DropConstraint(fkc))
        for table in tbs:
            conn.execute(DropTable(table))
        for custom_type in types:
            custom_type.drop(conn)
        trans.commit()
    except:
        trans.rollback()
        raise


class Sqla(Cli):
    'SQLAlchemy database handling'

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
                    # XXX Output of schema is commented since it doesn't work
                    # for dialect-specific things.
                    #print('{0}: {1}\n{2}'.format(engine, table.name, self._schema(table)))
                    metadata.create_all(engine, tables=[table])

    def command_drop_tables(self):
        answer = raw_input('All data will lost. Are you sure? [y/N] ')
        if answer.strip().lower()!='y':
            sys.exit('Interrupted')
        print('Droping table(s)...')
        for metadata, engines in self._get_binds().items():
            for engine in engines:
                print('... in {0}'.format(engine.url))
                drop_everything(engine)
        print('Done')

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
