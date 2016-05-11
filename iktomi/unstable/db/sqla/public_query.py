from sqlalchemy.orm.query import Query
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql import ClauseElement, Join
from sqlalchemy.sql.selectable import FromGrouping
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

    property_name = 'public'

    def get(self, ident):
        prop = self.property_name
        if self._criterion: # pragma: no cover
            mapper = self._only_full_mapper_zero("get")
            # Don't use getattr/hasattr to check public existence, since this
            # might misinterpret a bug (AttributeError raised by some code in
            # property implementation) as missing attribute and cause all
            # private data going to public.
            if prop in dir(mapper.class_):
                crit = getattr(mapper.class_, prop)
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
        if obj is not None and (prop not in dir(obj) or getattr(obj, prop)):
            return obj

    def __iter__(self):
        return Query.__iter__(self.private())

    def from_self(self, *ent):
        # override from_self() to automatically apply
        # the criterion too.   this works with count() and
        # others.
        return Query.from_self(self.private(), *ent)

    def with_entities(self, *entities):
        return Query.with_entities(self.private(), *entities)

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

    def _entity_criterion(self, entity):
        #if hasattr(entity, "property"):
        #    entity = entity.property.mapper
        if hasattr(entity, 'parententity'):
            # XXX is this used?
            entity = entity.parententity
        try:
            cls = _class_to_mapper(entity).class_
        except AttributeError:
            # XXX For tables, table columns
            #pass
            raise # XXX temporal, to verify it's used
        else:
            alias = entity if isinstance(entity, AliasedClass) else cls
            prop = self.property_name
            if prop in dir(cls):
                crit = getattr(alias, prop)
                if crit is not None:
                    if not isinstance(crit, ClauseElement):
                        # This simplest safe way to make bare boolean column
                        # accepted as expression.
                        crit = cast(crit, Boolean)
                    return crit
        return None

    def _add_entity_criterion(self, entity):
        crit = self._entity_criterion(entity)
        if crit is not None:
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

    def _add_eager_onclause(self, obj, selectable, crit):
        # be careful! should return anything only if the criterion has been
        # applied already
        if isinstance(obj, Join):
            if obj is selectable or obj.right == selectable:
                obj = obj._clone()
                obj.onclause = obj.onclause & crit
                return obj
            left = self._add_eager_onclause(obj.left, selectable, crit)
            if left is not None:
                obj = obj._clone()
                obj.left = left
                return obj
            right = self._add_eager_onclause(obj.right, selectable, crit)
            if right is not None:
                obj = obj._clone()
                obj.right = right
                return obj
        if isinstance(obj, FromGrouping):
            # XXX tests required!
            element = self._add_eager_onclause(obj.element, selectable, crit)
            if element is not None:
                obj = obj._clone()
                obj.element = element
                return obj
        return None

    def _add_eager_criterion(self, context, statement):
        for attr, value in context.attributes.items():
            if type(attr) is tuple and attr[0] == 'eager_row_processor':
                mapper, prop = attr[1]
                alias = value.aliased_class
                crit = self._entity_criterion(alias)
                if crit is not None:
                    # add criterion to join "on" clause because if we add it
                    # to where clause we filter out objects with related 
                    # unpublished and only unpublished items
                    statement = statement._clone()
                    new_from_obj = []
                    for obj in statement._from_obj:
                        selectable = alias._aliased_insp.selectable
                        new_obj = self._add_eager_onclause(obj, selectable, crit)
                        obj = new_obj if new_obj is not None else obj
                        new_from_obj.append(obj)
                    statement._from_obj = type(statement._from_obj)(new_from_obj)
        return statement

    def _simple_statement(self, context):
        # fixing joined load
        # XXX is this solution correct?
        statement = Query._simple_statement(self, context)
        return self._add_eager_criterion(context, statement)

    def _compound_eager_statement(self, context):
        # fixing joined load
        # XXX not tested! What is condition when this method is called
        statement = Query._compound_eager_statement(self, context)
        return self._add_eager_criterion(context, statement)
