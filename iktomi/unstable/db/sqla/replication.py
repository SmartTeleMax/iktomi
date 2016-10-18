'''
Functions for application-level replication.

Therminology:

reflect::
    Find an object with the same identifier in the target database without
    changing or creating it.
replicate::
    Find or create new object with the same identifier in the target database
    and update it with data of the current object. Only SQLAlchemy attributes
    found in both source and target classes are copied. For objects found via
    relationships the following rules apply: private ones are replecated and
    references to independent objects are reflected.
'''

from weakref import WeakSet
from sqlalchemy.schema import Column
from sqlalchemy.util import duck_type_collection
from sqlalchemy.orm import object_session
from sqlalchemy.orm.util import identity_key
from sqlalchemy.orm.attributes import manager_of_class, QueryableAttribute
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.collections import collection_adapter
from sqlalchemy.orm.attributes import instance_state, instance_dict
from sqlalchemy.orm.interfaces import MANYTOMANY, MANYTOONE, ONETOMANY


_included = WeakSet()
_excluded = WeakSet()


def include(prop):
    '''Replicate property that is normally not replicated. Right now it's
    meaningful for one-to-many relations only.'''
    if isinstance(prop, QueryableAttribute):
        prop = prop.property
    assert isinstance(prop, (Column, ColumnProperty, RelationshipProperty))
    #assert isinstance(prop, RelationshipProperty)
    _included.add(prop)

def exclude(prop):
    '''Don't replicate property that is normally replicated: ordering column,
    many-to-one relation that is marked for replication from other side.'''
    if isinstance(prop, QueryableAttribute):
        prop = prop.property
    assert isinstance(prop, (Column, ColumnProperty, RelationshipProperty))
    _excluded.add(prop)
    if isinstance(prop, RelationshipProperty):
        # Also exclude columns that participate in this relationship
        for local in prop.local_columns:
            _excluded.add(local)


def reflect(source, model, cache=None):
    '''Finds an object of class `model` with the same identifier as the
    `source` object'''
    if source is None:
        return None
    if cache and source in cache:
        return cache[source]
    db = object_session(source)
    ident = identity_key(instance=source)[1]
    assert ident is not None
    return db.query(model).get(ident)


class _PrimaryKeyIsNull(BaseException):
    '''Used when setting relationship property to None if this causes setting
    not nullable primary key column to NULL. Such objects should be skipped
    from replicate_filter.'''


def replicate_relation(source, target, attr, target_attr, cache=None):
    if attr.property.cascade.delete_orphan:
        process_scalar = replicate_no_merge
        process_list = replicate_filter
    else:
        process_scalar = reflect
        process_list = reflect_filter
    value = getattr(source, attr.key)
    target_attr_model = target_attr.property.mapper.class_
    if attr.property.uselist:
        adapter = collection_adapter(value)
        if adapter:
            # XXX The magic passes below are adapted from logic in
            # CollectionAttributeImpl.set() method without proper
            # understanding.  The `elif` branch isn't even coverered by tests.
            if hasattr(value, '_sa_iterator'):
                value = value._sa_iterator()
            elif duck_type_collection(value) is dict:
                value = value.values()
        reflection = process_list(value, target_attr_model, cache=cache)
        impl = instance_state(target).get_impl(attr.key)
        impl.set(instance_state(target), instance_dict(target), reflection,
                 # XXX We either have to convert reflection back to original
                 # collection type or use this private parameter.
                 _adapt=False)
    else:
        reflection = process_scalar(value, target_attr_model, cache=cache)
        setattr(target, attr.key, reflection)
        if (reflection is None and
                attr.property.direction is MANYTOONE and
                any(col.primary_key and not col.nullable
                    for col in attr.property.local_columns)):
            raise _PrimaryKeyIsNull()


def is_relation_replicatable(attr):
    if attr.property in _included:
        return True
    elif attr.property in _excluded:
        return False
    elif attr.property.viewonly:
        return False
    elif attr.property.cascade.delete_orphan:
        # Private, replicate
        return True
    elif attr.property.direction is MANYTOMANY:
        # Many-to-many. Usualy one side is short list and other is long or
        # absent. Reflect if not dynamic, other cases should be excluded
        # manually.
        assert attr.property.lazy in (True, False, 'dynamic')
        return attr.property.lazy!='dynamic'
    elif attr.property.direction is MANYTOONE:
        # Many-to-one and one-to-one with FK pointing from from this side to
        # other.
        return True
    else:
        assert attr.property.direction is ONETOMANY
        return False


def _column_property_in_registry(prop, registry):
    if prop in registry:
        return True
    elif len(prop.columns)==1:
        # Column() is translated to ColumnProperty with single column
        return prop.columns[0] in registry
    else:
        return False


def replicate_attributes(source, target, cache=None):
    '''Replicates common SQLAlchemy attributes from the `source` object to the
    `target` object.'''
    target_manager = manager_of_class(type(target))
    column_attrs = set()
    relationship_attrs = set()
    relationship_columns = set()
    for attr in manager_of_class(type(source)).attributes:
        if attr.key not in target_manager:
            # It's not common attribute
            continue
        target_attr = target_manager[attr.key]
        if isinstance(attr.property, ColumnProperty):
            assert isinstance(target_attr.property, ColumnProperty)
            column_attrs.add(attr)
        elif isinstance(attr.property, RelationshipProperty):
            assert isinstance(target_attr.property, RelationshipProperty)
            relationship_attrs.add(attr)
            if attr.property.direction is MANYTOONE:
                relationship_columns.update(attr.property.local_columns)
    for attr in column_attrs:
        if _column_property_in_registry(attr.property, _excluded):
            continue
        elif (not _column_property_in_registry(attr.property, _included) and
                 all(column in relationship_columns
                     for column in attr.property.columns)):
            continue
        setattr(target, attr.key, getattr(source, attr.key))
    for attr in relationship_attrs:
        target_attr_model = target_manager[attr.key].property.argument
        if not is_relation_replicatable(attr):
            continue
        replicate_relation(source, target, attr, target_manager[attr.key],
                           cache=cache)


def replicate_no_merge(source, model, cache=None):
    '''Replicates the `source` object to `model` class and returns its
    reflection.'''
    # `cache` is used to break circular dependency: we need to replicate
    # attributes before merging target into the session, but replication of
    # some attributes may require target to be in session to avoid infinite
    # loop.
    if source is None:
        return None
    if cache is None:
        cache = {}
    elif source in cache:
        return cache[source]
    db = object_session(source)
    cls, ident = identity_key(instance=source)
    target = db.query(model).get(ident)
    if target is None:
        target = model()
    cache[source] = target
    try:
        replicate_attributes(source, target, cache=cache)
    except _PrimaryKeyIsNull:
        return None
    else:
        return target


def replicate(source, model, cache=None):
    '''Replicates the `source` object to `model` class and returns its
    reflection.'''
    target = replicate_no_merge(source, model, cache=cache)
    if target is not None:
        db = object_session(source)
        target = db.merge(target)
    return target


def replicate_filter(sources, model, cache=None):
    '''Replicates the list of objects to other class and returns their
    reflections'''
    targets = [replicate_no_merge(source, model, cache=cache)
               for source in sources]
    # Some objects may not be available in target DB (not published), so we
    # have to exclude None from the list.
    return [target for target in targets if target is not None]


def reflect_filter(sources, model, cache=None):
    '''Returns the list of reflections of objects in the `source` list to other
    class. Objects that are not found in target table are silently discarded.
    '''
    targets = [reflect(source, model, cache=cache) for source in sources]
    # Some objects may not be available in target DB (not published), so we
    # have to exclude None from the list.
    return [target for target in targets if target is not None]
