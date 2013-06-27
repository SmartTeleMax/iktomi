from sqlalchemy.orm.query import Query
from sqlalchemy.sql import ClauseElement
from sqlalchemy import cast, Boolean
from sqlalchemy.orm.util import _class_to_mapper


class PublicQuery(Query):

    '''
    Filters all queries by publicity condition for each participating mapped
    class. Attribute "public" of mapped class (if present) should be either
    boolean column or @hybrid_property providing publicity criterion clause for
    the class and boolean (convertable to boolean) value for instance of the
    class.

    A version from recipe combined with our own vision
    http://www.sqlalchemy.org/trac/wiki/UsageRecipes/PreFilteredQuery
    '''

    def get(self, ident):
        if self._criterion:
            mapper = self._only_full_mapper_zero("get")
            # Don't use getattr/hasattr to check public existence, since this
            # might misinterpret a bug (AttributeError raised by some code in
            # property implementation) as missing attribute and cause all
            # private data going to public.
            if 'public' in dir(mapper.class_):
                crit = mapper.class_.public
                if crit is not None:
                    if not isinstance(crit, ClauseElement):
                        # This simplest safe way to make bare boolean column
                        # accepted as expression.
                        crit = cast(crit, Boolean)
                    if crit!=self._criterion:
                        # We can't verify that criterion is from our private()
                        # call.  Check from DB instead of looking in identity
                        # map.
                        assert False # XXX temporal to verify it's used
                        return Query.get(self.populate_existing(), ident)
            assert False # XXX temporal to verify it's used
        obj = Query.get(self, ident)
        if obj is not None and ('public' not in dir(obj) or obj.public):
            return obj

    def __iter__(self):
        return Query.__iter__(self.private())

    def from_self(self, *ent):
        # override from_self() to automatically apply
        # the criterion too.   this works with count() and
        # others.
        return Query.from_self(self.private(), *ent)

    def count(self):
        # Without it it works with slow implementation of count(), while
        # we often use a faster one from older version.
        return Query.count(self.private())

    def slice(self, start, stop):
        return Query.slice(self.private(), start, stop)

    def limit(self, limit):
        return Query.limit(self.private(), limit)

    def offset(self, offset):
        return Query.offset(self.private(), offset)

    def _add_entity_criterion(self, entity):
        #if hasattr(entity, "property"):
        #    entity = entity.property.mapper
        if hasattr(entity, 'parententity'):
            entity = entity.parententity
        try:
            cls = _class_to_mapper(entity).class_
        except AttributeError:
            # XXX For tables, table columns
            #pass
            raise # XXX temporal, to verify it's used
        else:
            if 'public' in dir(cls):
                crit = cls.public
                if crit is not None:
                    if not isinstance(crit, ClauseElement):
                        # This simplest safe way to make bare boolean column
                        # accepted as expression.
                        crit = cast(crit, Boolean)
                    return self.filter(crit)
        return self

    def private(self):
        if self._limit is not None or self._offset is not None \
                or self._statement is not None:
            # Conditions must be added just before setting LIMIT and OFFSET
            # Calling it with statement means from_statement was used: either
            # manually (it's your problem) or by load_scalar_attributes (no
            # need in filtering here).
            return self
        query = self
        for query_entity in self._entities:
            for entity in query_entity.entities:
                query = query._add_entity_criterion(entity)
        for entity in self._join_entities:
            query = query._add_entity_criterion(entity)
        return query
