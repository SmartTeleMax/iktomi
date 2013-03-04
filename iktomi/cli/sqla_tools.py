# -*- coding: utf-8 -*-

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


#NOTE: this recipe taken from
#      http://www.sqlalchemy.org/trac/wiki/UsageRecipes/DropEverything
def gentle_drop_tables(engine):
    conn = engine.connect()

    # the transaction only applies if the DB supports
    # transactional DDL, i.e. Postgresql, MS SQL Server
    trans = conn.begin()

    inspector = reflection.Inspector.from_engine(engine)

    # gather all data first before dropping anything
    # some DBs lock after things have been dropped in
    # a transaction.

    metadata = MetaData()

    tbs = []
    all_fks = []
    types = []

    for table_name in inspector.get_table_names():
        fks = []
        for fk in inspector.get_foreign_keys(table_name):
            if not fk['name']:
                continue
            fks.append(
                ForeignKeyConstraint((),(),name=fk['name'])
                )
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


def recreate_schema(databases, models_location='models', engine_params=None):
    engine_params = engine_params or {}
    databases = databases if isinstance(databases, dict) else {'': databases}
    for ref, uri in databases.items():
        md_ref = '.'.join(filter(None, [models_location, ref]))
        metadata = getattr(__import__(md_ref, None, None, ['*']), 'metadata')
        engine = create_engine(uri, **engine_params)
        print '[%s]' % uri, 'gentle drop tables...'
        gentle_drop_tables(engine)
        print '[%s]' % uri, 'creating tables...'
        metadata.create_all(engine)
        print '[%s]' % uri, 'done'
