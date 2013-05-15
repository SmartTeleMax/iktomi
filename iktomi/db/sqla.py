# -*- coding: utf-8 -*-

import logging
from sqlalchemy import orm, types, create_engine
from sqlalchemy.orm.query import Query
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
                  session_class=DBSession):
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
        engine.logger = logging.getLogger('sqlalchemy.engine.[%s]' % ref)
        for table in metadata.sorted_tables:
            binds[table] = engine
    return orm.sessionmaker(class_=session_class, query_cls=query_cls,
                            binds=binds, **session_params)


class StringList(types.TypeDecorator):

    impl = types.String

    def process_bind_param(self, value, dialect):
        if value is not None:
            return ','.join(value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return filter(None, value.split(','))


class IntegerList(types.TypeDecorator):

    impl = types.String

    def process_bind_param(self, value, dialect):
        if value is not None:
            return ','.join(str(item) for item in value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return [int(item) for item in value.split(',') if item]


try:
    from jinja2 import Markup
except ImportError:
    pass
else:
    Markup = None


class HtmlBase(types.TypeDecorator):
    '''Base class for HTML markup types (safe to render in template)'''

    markup_class = Markup

    def process_result_value(self, value, dialect):
        if value is not None:
            return self.markup_class(value)

    def process_bind_param(self, value, dialect):
        if value is not None:
            return unicode(value)


class Html(HtmlBase):
    '''
    Factory class for HTML type. Usage:
        Column(Html(Text))
        Column(Html(String(1000)))
        Column(Html(BigText, markup_class=SomeWrapperClass))
    '''

    def __init__(self, _impl, markup_class=Markup):
        if callable(_impl):
            _impl = _impl()
        self.impl = _impl
        self.markup_class = markup_class
        # Don't call base class' __init__ since we reimplemented it in a
        # different way.


# Compatibility classes. Deprecate them?

class HtmlString(HtmlBase):
    impl = types.String

class HtmlText(HtmlBase):
    impl = types.Text
