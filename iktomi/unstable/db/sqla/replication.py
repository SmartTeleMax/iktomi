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

from sqlalchemy.orm import object_session
from sqlalchemy.orm.util import identity_key
from sqlalchemy.orm.attributes import manager_of_class
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy import Boolean


def reflect(source, model):
    '''Finds an object of class `model` with the same identifier as the
    `source` object'''
    db = object_session(source)
    ident = identity_key(instance=source)[1]
    assert ident is not None
    return db.query(model).get(ident)

def replicate_attributes(source, target):
    '''Replicates common SQLAlchemy attributes from the `source` object to the
    `target` object.'''
    target_manager = manager_of_class(type(target))
    for attr in manager_of_class(type(source)).attributes:
        if attr.key not in target_manager:
            # It's not common attribute
            continue
        target_attr = target_manager[attr.key]
        if isinstance(attr.property, ColumnProperty):
            assert isinstance(target_attr.property, ColumnProperty)
            setattr(target, attr.key, getattr(source, attr.key))
        elif isinstance(attr.property, RelationshipProperty):
            assert isinstance(target_attr.property, RelationshipProperty)
            target_attr_model = target_attr.property.argument
            value = getattr(source, attr.key)
            if attr.property.cascade.delete_orphan:
                # Private, replicate
                if attr.property.uselist:
                    adapter = collection_adapter(value)
                    if adapter:
                        # Convert any collection to flat iterable
                        value = adapter.adapt_like_to_iterable(value)
                    reflection = replicate_filter(value, target_attr_model)
                    impl = instance_state(target).get_impl(attr.key)
                    # Set any collection value from flat list
                    impl._set_iterable(instance_state(target),
                                       instance_dict(target),
                                       reflection)
                else:
                    reflection = target_attr_model()
                    replicate_attributes(value, reflection)
                    setattr(target, attr.key, reflection)
            elif attr.property.secondary is not None:
                # Many-to-many, reflect
                reflection = reflect_filter(value, target_attr_model)
                setattr(target, attr.key, reflection)

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
