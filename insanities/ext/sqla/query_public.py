from sqlalchemy.orm.query import Query, _generative
from sqlalchemy.orm.util import _class_to_mapper


class QueryPublic(Query):
    def __init__(self, entities, *args, **kwargs):
        # XXX I'm not sure that multiple statements are safe. For example:
        # db.query(Model1, Model2.title)
        assert len(entities)==1, entities

        super(QueryPublic, self).__init__(entities, *args, **kwargs)

        # Copypasted from Query.with_polymorphic
        # XXX fails when entity is QueryableAttribute or other no-mapped object
        entity = self._generate_mapper_zero()
        entity.set_with_polymorphic(self, '*',
                                    selectable=None, discriminator=None)

        # XXX Sometimes it's not a model class or mapper, so the following fails.
        # can be also QueryableAttribute, AliasedClass, expression._Label, etc
        cls = _class_to_mapper(entities[0]).class_
        self._public_condition = getattr(cls, 'public_condition', None)
        if self._public_condition is not None:

            self._criterion = self.filter(self._public_condition)._criterion

    def get(self, ident):
        # Use default implementation when there is no condition
        if not self._criterion:
            return Query.get(self, ident)

        # Copied from Query implementation with some changes.
        if hasattr(ident, '__composite_values__'):
            ident = ident.__composite_values__()
        mapper = self._only_mapper_zero(
                    "get() can only be used against a single mapped class.")
        key = mapper.identity_key_from_primary_key(ident)
        if ident is None:
            if key is not None:
                ident = key[1]
        else:
            from sqlalchemy import util
            ident = util.to_list(ident)
        if ident is not None:
            columns = list(mapper.primary_key)
            if len(columns)!=len(ident):
                raise TypeError("Number of values doesn't match number "
                                'of columns in primary key')
            params = {}
            for column, value in zip(columns, ident):
                params[column.key] = value
            return self.filter_by(**params).first()
    
    # Commented since not used. This method is needed when with_polymorphic is
    # not set. In this case sqlalchemy calls from_statement to deferred attrs load
    # In current version with_polymorphic is always set to *, so this metyhod is
    # unnecessary
    #@_generative() #removed assertations
    #def from_statement(self, statement):
        # we don't want allow this method for external use:
        # it can not use public_condition and therefore it's unsafe.
        # But sqlalchemy uses it when loads attributes for inherited classes
        # and we can't simply disallow it.
        # So we have to check if it is used by safe method
        #def _search_in_caller_names(name):
        #    '''checks if function named `name` is in caller's stack'''
        #    import sys
        #    frame = sys._getframe(1)    # also there is logger.currentframe function
        #    while frame:
        #        if frame.f_code.co_name == name:
        #            return True
        #        frame = frame.f_back
        #
        #check_stack = _search_in_caller_names('_load_scalar_attributes')
        #assert check_stack, 'For safity reasons this method can be used only '\
        #                    'for retrieving attributes of inherited models'
        #
        ## Copied from Query
        #from sqlalchemy.sql import expression
        #if isinstance(statement, basestring):
       #    statement = sql.text(statement)
        #
        #if not isinstance(statement, (expression._TextClause, expression._SelectBaseMixin)):
        #    raise sa_exc.ArgumentError("from_statement accepts text(), select(), and union() objects only.")
        #self._statement = statement
        ## set _criterion to none since sqlalchemy's from_statement doesn't accept them
        #self._criterion = None
