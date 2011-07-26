# -*- codingL: utf-8 -*-

from sqlalchemy import orm, types, create_engine
from sqlalchemy.orm.query import Query
from insanities.utils import cached_property, import_string


class DBSession(orm.session.Session):

    def get(self, query, **kwargs):
        if not isinstance(query, Query):
            query = self.query(query)
        if kwargs:
            query = query.filter_by(**kwargs)
        return query.first()

    #TODO: implement `get_or_404`


def session_maker(databases, query_cls=Query, engine_params=None,
                  session_class=DBSession):
    engine_params = engine_params or {}
    db_dict = {}
    if isinstance(databases, basestring):
        engine = create_engine(databases, **engine_params)
        return orm.sessionmaker(class_=session_class, query_cls=query_cls,
                                bind=engine, autoflush=False)
    for ref, uri in databases.items():
        md_ref = '.'.join(filter(None, ['models', ref]))
        metadata = import_string(md_ref, 'metadata')
        engine = create_engine(uri, **engine_params)
        #TODO: find out why this is broken since sqlalchemy 0.7
        #engine.logger.logger.name += '(%s)' % ref
        for table in metadata.sorted_tables:
            db_dict[table] = engine
    return orm.sessionmaker(class_=session_class, query_cls=query_cls, binds=db_dict,
                            autoflush=False)


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


def get_html_class(safe_marker, impl_=types.Text):

    class HtmlText(types.TypeDecorator):
        '''Represants safe to render in template html markup'''

        impl = impl_

        def process_result_value(self, value, dialect):
            if value is not None:
                return safe_marker(value)

        def process_bind_param(self, value, dialect):
            if value is not None:
                return unicode(value)

    return HtmlText

try:
    from jinja2 import Markup
except ImportError:
    pass
else:
    HtmlText = get_html_class(Markup)
    HtmlString = get_html_class(Markup, impl_=types.String)

