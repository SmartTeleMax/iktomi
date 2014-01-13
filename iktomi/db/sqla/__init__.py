# -*- coding: utf-8 -*-

import logging
from sqlalchemy import orm, create_engine
from sqlalchemy.orm.query import Query
from iktomi.utils import import_string
from iktomi.utils.deprecation import deprecated


class DBSession(orm.session.Session):

    @deprecated('Use Session.query(cls).filter_by(…).scalar() instead.')
    def get(self, query, **kwargs):
        if not isinstance(query, Query):
            query = self.query(query)
        if kwargs:
            query = query.filter_by(**kwargs)
        return query.first()


def multidb_binds(databases, package=None, engine_params=None):
    '''Creates dictionary to be passed as `binds` parameter to
    `sqlalchemy.orm.sessionmaker()` from dictionary mapping models module name
    to connection URI that should be used for these models. Models module must
    have `metadata` attribute. `package` when set must be a package or package
    name for all models modules.'''
    engine_params = engine_params or {}
    if not (package is None or isinstance(package, basestring)):
        package = getattr(package, '__package__', None) or package.__name__
    binds = {}
    for ref, uri in databases.items():
        md_ref = '.'.join(filter(None, [package, ref]))
        metadata = import_string(md_ref, 'metadata')
        engine = create_engine(uri, **engine_params)
        # Dot before [name] is required to allow setting logging level etc. for
        # all them at once.
        engine.logger = logging.getLogger('sqlalchemy.engine.[%s]' % ref)
        for table in metadata.sorted_tables:
            binds[table] = engine
    return binds


@deprecated('Use sqlalchemy.orm.sessionmaker(binds=multidb_binds(…)) instead.')
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
    if isinstance(databases, basestring):
        engine = create_engine(databases, **engine_params)
        return orm.sessionmaker(class_=session_class, query_cls=query_cls,
                                bind=engine, **session_params)
    binds = multidb_binds(databases, models_location, engine_params=engine_params)
    return orm.sessionmaker(class_=session_class, query_cls=query_cls,
                            binds=binds, **session_params)
