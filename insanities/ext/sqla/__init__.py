#__all__ = ['Integer', 'String', 'Text', 'Boolean', 'Date', 'DateTime',
#           'StringList', 'IntegerList', 'VarBinary', 'MediumText',
#           'AlchemyFile', 'AlchemyImageFile',
#           'ForeignKey', 'Column', 'Table',
#           'PrimaryKeyConstraint', 'ForeignKeyConstraint', 'UniqueConstraint',
#           'relation', 'association_proxy', 'composite',
#           'object_session', 'DeclarativeMeta',
#           'asc', 'desc', 'func',
#           'HtmlText', 'HtmlMediumText', 'HtmlString']

from sqlalchemy import Column, ForeignKey
from sqlalchemy import Table as _SA_Table
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint, \
                       ForeignKeyConstraint
from sqlalchemy.databases.mysql import MSMediumText as MediumText
from sqlalchemy import asc, desc, func
from sqlalchemy.orm import object_session, class_mapper, composite, relation
from sqlalchemy.orm.query import Query, _generative
from sqlalchemy.orm.util import _class_to_mapper, identity_key
from sqlalchemy.orm.attributes import instance_state, manager_of_class
from sqlalchemy.orm.properties import PropertyLoader
from sqlalchemy import orm, types, create_engine
from sqlalchemy.ext import declarative
from sqlalchemy.ext.associationproxy import association_proxy
from insanities.utils import cached_property
from insanities.forms.files import AlchemyFile as _AlchemyFile, \
                                   AlchemyImageFile as _AlchemyImageFile

from insanities.web import HttpException, ContinueRoute, Wrapper

_default_table_kwargs = {
    'mysql_engine': 'InnoDB',
    'mysql_default charset': 'utf8',
}

def Table(*args, **kwargs):
    kwargs = dict(_default_table_kwargs, **kwargs)
    return _SA_Table(*args, **kwargs)

class DeclarativeMeta(declarative.DeclarativeMeta):

    # XXX is it needed?
    def __init__(cls, classname, bases, dict_):
        # Do not extend base class
        if '_decl_class_registry' not in cls.__dict__:
            # Lookup __dict__, since __tablename__ should change after
            # inheritance.
            if '__tablename__' not in cls.__dict__:
                cls.__tablename__ = classname
            cls.metadata.__dict__.setdefault('_mapped_models', set()).add(cls)
            extension_methods = set(['on_delete', 'on_update', 'pre_update'])
            if set(dir(cls)) & extension_methods:
                mapper_args = getattr(cls, '__mapper_args__', {})
                # Set attribute in this class. Don't update inline, since it
                # can come from parent.
                cls.__mapper_args__ = mapper_args
                ext = mapper_args.get('extension', [])
                if isinstance(ext, orm.MapperExtension):
                    ext = [ext]
                if on_change_extension not in ext:
                    ext.append(on_change_extension)
                mapper_args['extension'] = ext
            if cls.__tablename__ is None:
                # Special case: single table inheritance
                del cls.__tablename__
            else:
                table_args = getattr(cls, '__table_args__', {})
                if isinstance(table_args, dict):
                    table_kwargs = dict(_default_table_kwargs, **table_args)
                    cls.__table_args__ = table_kwargs
                else:
                    table_kwargs = dict(_default_table_kwargs, **table_args[-1])
                    cls.__table_args__ = table_args[:-1] + (table_kwargs,)
        return super(DeclarativeMeta, cls).__init__(classname, bases, dict_)


class DBSession(orm.session.Session):

    # This is not needed anymore since we pass models in binds too.
    #def get_bind(self, mapper, clause=None):
    #    from sqlalchemy.orm.util import _class_to_mapper
    #    # Workaround a bug in SQLAlchemy which can't find a bind when a
    #    # mapped_table is a Join object (for inheritted models).
    #    if mapper is not None and clause is None:
    #        c_mapper = _class_to_mapper(mapper)
    #        if hasattr(c_mapper, 'mapped_table'):
    #            clause = mapper.mapped_table
    #    return orm.session.Session.get_bind(self, mapper, clause)

    #def __init__(self, *args, **kwargs):
    #    self._delayed_actions = []
    #    orm.session.Session.__init__(self, *args, **kwargs)
    #
    #def flush(self):
    #    orm.session.Session.flush(self)
    #    for attempt in xrange(5):
    #        if self._delayed_actions:
    #            while self._delayed_actions:
    #                action = self._delayed_actions.pop(0)
    #                action()
    #            orm.session.Session.flush(self)
    #        if not self.dirty:
    #            break
    #        self.identity_map.modified = True
    #        orm.session.Session.flush(self)
    #    else:
    #        raise RuntimeError('Failed to flush session in 5 attempts')

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
    
    def __init__(self, uris, models, query_cls=Query, class_=DBSession,
                 engine_params={}):
        super(SqlAlchemy, self).__init__()
        
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
        rctx.db = self.maker()
        rctx = self.next(rctx)
        rctx.db.close()
        return rctx
