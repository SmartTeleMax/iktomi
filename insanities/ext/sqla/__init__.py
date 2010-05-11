
from sqlalchemy import orm, types, create_engine
from sqlalchemy.ext import declarative
from sqlalchemy.orm.query import Query

from insanities.utils import cached_property
from insanities.web import HttpException, ContinueRoute, Wrapper


class DBSession(orm.session.Session):

    # XXX delayed actions are also implemented in one of projects

    def get(self, query, **kwargs):
        if not isinstance(query, Query):
            query = self.query(query)
        if kwargs:
            query = query.filter_by(**kwargs)
        return query.first()

    def get_or_404(self, query, **kwargs):
        obj = self.get(query, **kwargs)
        if obj is None:
            raise HttpException(404)
        return obj


class SqlAlchemy(Wrapper):

    def __init__(self, uris, models, param_name='db', query_cls=Query, class_=DBSession,
                 engine_params={}):
        super(SqlAlchemy, self).__init__()
        self.param_name = param_name

        db_dict = {}
        for ref, uri in uris.items():
            models_module = ref and getattr(models, ref) or models
            metadata = models_module.metadata

            engine = create_engine(uri, **engine_params)
            engine.logger.name += '(%s)' % ref

            for table in metadata.sorted_tables:
                db_dict[table] = engine
            for model in getattr(metadata, '_mapped_models', []):
                db_dict[model] = engine
        self.maker = orm.sessionmaker(class_=class_, query_cls=query_cls,
                                      binds=db_dict, autoflush=False,
                                      autocommit=False)

    def handle(self, rctx):
        # XXX should be lazy
        db = self.maker()
        rctx.vals[self.param_name] = db
        try:
            rctx = self.exec_wrapped(rctx)
        finally:
            db.close()
        return rctx
