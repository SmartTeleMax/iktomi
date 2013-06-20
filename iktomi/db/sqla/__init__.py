# -*- coding: utf-8 -*-

import logging
from sqlalchemy import orm, create_engine
from sqlalchemy.orm.query import Query
from sqlalchemy.ext import declarative
from iktomi.utils import cached_property, import_string
from iktomi.utils.deprecation import deprecated


class DBSession(orm.session.Session):

    @deprecated('Use Session.query(cls).filter_by(…).scalar() instead.')
    def get(self, query, **kwargs):
        if not isinstance(query, Query):
            query = self.query(query)
        if kwargs:
            query = query.filter_by(**kwargs)
        return query.first()


def session_maker(databases, query_cls=Query, models_location='models',
                  engine_params=None, session_params=None,
                  session_class=orm.session.Session):
    '''
    Session maker with multiple databases support. For each database there
    should be corresponding submodule of `models_location` package with
    `metadata` object for that database.
    '''
    engine_params = engine_params or {}
    session_params = dict(session_params or {})
    session_params.setdefault('autoflush', False)
    binds = {}
    if isinstance(databases, basestring):
        engine = create_engine(databases, **engine_params)
        return orm.sessionmaker(class_=session_class, query_cls=query_cls,
                                bind=engine, **session_params)
    for ref, uri in databases.items():
        md_ref = '.'.join(filter(None, [models_location, ref]))
        metadata = import_string(md_ref, 'metadata')
        engine = create_engine(uri, **engine_params)
        # Dot before [name] is required to allow setting logging level etc. for
        # all them at once.
        engine.logger = logging.getLogger('sqlalchemy.engine.[%s]' % ref)
        for table in metadata.sorted_tables:
            binds[table] = engine
    return orm.sessionmaker(class_=session_class, query_cls=query_cls,
                            binds=binds, **session_params)


class AutoTableNameMeta(declarative.DeclarativeMeta):

    def __init__(cls, name, bases, dict_):
        super(AutoTableNameMeta, cls).__init__(name, bases, dict_)
        if '_decl_class_registry' in cls.__dict__:
            # Do not extend base class
            return
        # Lookup __dict__ and not attribute directly since __tablename__
        # should change on inheritance.
        if '__tablename__' not in cls.__dict__ and \
                not cls.__dict__.get('__abstract__', False):
            cls.__tablename__ = classname
        # XXX Commented untill we write the reason in comments
        #elif cls.__tablename__ is None:
        #    del cls.__tablename__


def table_args_meta(table_args):

    class TableArgsMeta(declarative.DeclarativeMeta):

        def __init__(cls, name, bases, dict_):
            super(TableArgsMeta, cls).__init__(name, bases, dict_)
            if '_decl_class_registry' in cls.__dict__:
                # Do not extend base class
                return
            if cls.__dict__.get('__tablename__') and \
                    not cls.__dict__.get('__abstract__', False):
                ta = getattr(cls, '__table_args__', {})
                if isinstance(ta, dict):
                    ta = dict(table_args, **ta)
                    cls.__table_args__ = ta
                else:
                    ta = dict(table_args, **ta[-1])
                    cls.__table_args__ = ta[:-1] + (ta,)

    return TableArgsMeta
