# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import six
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
        t = Table(table_name, metadata, *fks)
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
    except: # pragma: no cover
        trans.rollback()
        raise


class Sqla(Cli):
    '''
    SQLAlchemy database handling

    :param session_maker: sqlalchemy session maker function
    :param metadata: sqlalchemy metadata object or dictionary mapping names to
        metadata objects for multi-DB configuration to deal with
    :param initial: a function acceptind sqlalchemy session and filling-in
        a database with default initial data
    :param dict generators: a dictionary with generator functions. Generator
        functions should fill database with "lorem ipsum" data.
        They accept sqlalchemy session and a cnumber of objects to be created.
    '''

    def __init__(self, session_maker, metadata, initial=None, generators=None):
        self.session = session_maker()
        self.metadata = metadata
        self.initial = initial
        self.generators = generators or {}

    def _schema(self, table):
        from sqlalchemy.schema import CreateTable
        engine = self.session.get_bind(clause=table)
        return six.text_type(CreateTable(table, bind=engine))

    def command_create_tables(self, meta_name=None, verbose=False):
        '''
        Create tables according sqlalchemy data model.

        Is not a complex migration tool like alembic, just creates tables that
        does not exist::

            ./manage.py sqla:create_tables [--verbose] [meta_name]
        '''

        def _create_metadata_tables(metadata):
            for table in metadata.sorted_tables:
                if verbose:
                    print(self._schema(table))
                else:
                    print('  '+table.name)
                engine = self.session.get_bind(clause=table)
                metadata.create_all(bind=engine, tables=[table])

        if isinstance(self.metadata, MetaData):
            print('Creating tables...')
            _create_metadata_tables(self.metadata)
        else:
            for current_meta_name, metadata in self.metadata.items():
                if meta_name not in (current_meta_name, None):
                    continue
                print('Creating tables for {}...'.format(current_meta_name))
                _create_metadata_tables(metadata)

    def command_drop_tables(self, meta_name=None):
        '''
        Drops all tables without dropping a database::

            ./manage.py sqla:drop_tables [meta_name]
        '''
        answer = six.moves.input(u'All data will lost. Are you sure? [y/N] ')

        if answer.strip().lower()!='y':
            sys.exit('Interrupted')

        def _drop_metadata_tables(metadata):
            table = next(six.itervalues(metadata.tables), None)
            if table is None:
                print('Failed to find engine')
            else:
                engine = self.session.get_bind(clause=table)
                drop_everything(engine)
                print('Done')

        if isinstance(self.metadata, MetaData):
            print('Droping tables... ', end='')
            _drop_metadata_tables(self.metadata)
        else:
            for current_meta_name, metadata in self.metadata.items():
                if meta_name not in (current_meta_name, None):
                    continue
                print('Droping tables for {}... '.format(current_meta_name),
                      end='')
                _drop_metadata_tables(metadata)

    def command_init(self):
        '''
        Runs init function::

            ./manage.py sqla:init
        '''
        if self.initial:
            self.initial(self.session)

    def command_reset(self):
        '''
        Drops all tables, creates tables and runs init function::

            ./manage.py sqla:reset
        '''
        self.command_drop_tables()
        self.command_create_tables()
        self.command_init()

    def command_schema(self, name=None):
        '''
        Prints current database schema (according sqlalchemy database model)::

            ./manage.py sqla:schema [name]
        '''
        meta_name = table_name = None
        if name:
            if isinstance(self.metadata, MetaData):
                table_name = name
            elif '.' in name:
                meta_name, table_name = name.split('.', 1)
            else:
                meta_name = name

        def _print_metadata_schema(metadata):
            if table_name is None:
                for table in metadata.sorted_tables:
                    print(self._schema(table))
            else:
                try:
                    table = metadata.tables[table_name]
                except KeyError:
                    sys.exit('Table {} is not found'.format(name))
                print(self._schema(table))

        if isinstance(self.metadata, MetaData):
            _print_metadata_schema(self.metadata)
        else:
            for current_meta_name, metadata in self.metadata.items():
                if meta_name not in (current_meta_name, None):
                    continue
                _print_metadata_schema(metadata)

    def command_gen(self, *names):
        '''
        Runs generator functions.

        Run `docs` generator function::

            ./manage.py sqla:gen docs

        Run `docs` generator function with `count=10`::

            ./manage.py sqla:gen docs:10
        '''
        if not names:
            sys.exit('Please provide generator names')
        for name in names:
            name, count = name, 0
            if ':' in name:
                name, count = name.split(':', 1)
            count = int(count)
            create = self.generators[name]
            print('Generating `{0}` count={1}'.format(name, count))
            create(self.session, count)
            self.session.commit()
