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
from sqlalchemy.orm import object_session
from sqlalchemy.orm.util import identity_key
from sqlalchemy.orm.attributes import manager_of_class
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.collections import collection_adapter
from sqlalchemy.orm.attributes import instance_state, instance_dict


_included = WeakSet()
_excluded = WeakSet()


def include(prop):
    '''Replicate property that is normally not replicated. Right now it's
    meaningful for one-to-many relations only.'''
    assert isinstance(prop, RelationshipProperty)
    _included.add(prop)

def exclude(prop):
    '''Don't replicate property that is normally replicated: ordering column,
    many-to-one relation that is marked for replication from other side.'''
    assert isinstance(prop, [Column, ColumnProperty, RelationshipProperty])
    _excluded.add(prop)
    if isinstance(prop, RelationshipProperty):
        # Also exclude columns that participate in this relationship
        for local, remote in prop.local_remote_pairs:
            _excluded.add(local)


def reflect(source, model):
    '''Finds an object of class `model` with the same identifier as the
    `source` object'''
    if source is None:
        return None
    db = object_session(source)
    ident = identity_key(instance=source)[1]
    assert ident is not None
    return db.query(model).get(ident)


def replicate_relation(source, target, attr, target_attr):
    if attr.property.cascade.delete_orphan:
        filter_one = replicate
        filter_list = replicate_filter
    else:
        filter_one = reflect
        filter_list = reflect_filter
    value = getattr(source, attr.key)
    target_attr_model = target_attr.property.mapper.class_
    if attr.property.uselist:
        adapter = collection_adapter(value)
        if adapter:
            # Convert any collection to flat iterable
            value = adapter.adapt_like_to_iterable(value)
        reflection = filter_list(value, target_attr_model)
        impl = instance_state(target).get_impl(attr.key)
        # Set any collection value from flat list
        impl._set_iterable(instance_state(target),
                           instance_dict(target),
                           reflection)
    else:
        reflection = filter_one(value, target_attr_model)
        setattr(target, attr.key, reflection)


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
    elif attr.property.secondary is not None:
        # Many-to-many. Usualy one side is short list and other is long or
        # absent. Reflect if not dynamic, other cases should be excluded
        # manually.
        assert attr.property.lazy in (True, False, 'dynamic')
        return attr.property.lazy!='dynamic'
    else:
        # Many-to-one, one-to-many, one-to-one. Reflect only if FK points from
        # from this side to other.
        # XXX Composite FKs are ignore (not replicated).
        if len(attr.property.local_remote_pairs)!=1:
            return False
        local, remote = attr.property.local_remote_pairs[0]
        for fk in local.foreign_keys:
            if fk.column==remote:
                return True
        else:
            return False


def _column_property_in_registry(prop, registry):
    if prop in registry:
        return True
    elif len(prop.columns)==1:
        # Column() is translated to ColumnProperty with single column
        return prop.columns[0] in registry
    else:
        return False


def replicate_attributes(source, target):
    '''Replicates common SQLAlchemy attributes from the `source` object to the
    `target` object.'''
    target_manager = manager_of_class(type(target))
    column_attrs = set()
    relationship_attrs = set()
    # XXX Temporary disabled till we find proper algorithm to determine
    # relationship columns that should be excluded.
    #relationship_columns = set()
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
            # XXX Temporary disabled till we find proper algorithm to determine
            # relationship columns that should be excluded.
            #for local, remote in attr.property.local_remote_pairs:
            #    relationship_columns.add(local)
    for attr in column_attrs:
        if _column_property_in_registry(attr.property, _excluded):
            continue
        # XXX Temporary disabled till we find proper algorithm to determine
        # relationship columns that should be excluded.
        #elif (not _column_property_in_registry(attr.property, _included) and
        #         all(column in relationship_columns
        #             for column in attr.property.columns)):
        #    continue
        setattr(target, attr.key, getattr(source, attr.key))
    for attr in relationship_attrs:
        target_attr_model = target_manager[attr.key].property.argument
        if is_relation_replicatable(attr):
            replicate_relation(source, target, attr, target_manager[attr.key])


def replicate(source, model):
    '''Replicates the `source` object to `model` class and returns its
    reflection.'''
    target = model()
    replicate_attributes(source, target)
    db = object_session(source)
    return db.merge(target)


def replicate_filter(sources, model):
    '''Replicates the list of objects to other class and returns their
    reflections'''
    targets = []
    for source in sources:
        assert filter(None, identity_key(instance=source))
        target = model()
        replicate_attributes(source, target)
        targets.append(target)
    return targets


def reflect_filter(sources, model):
    '''Returns the list of reflections of objects in the `source` list to other
    class. Objects that are not found in target table are silently discarded.
    '''
    targets = [reflect(source, model) for source in sources]
    # Some objects may not be available in target DB (not published), so we
    # have to exclude None from the list.
    return [target for target in targets if target is not None]