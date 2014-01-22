import os, errno, logging
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.interfaces import MapperProperty
from sqlalchemy.orm.attributes import get_history
from sqlalchemy import event
from sqlalchemy.util import set_creation_order
from weakref import WeakKeyDictionary
from ..files import TransientFile, PersistentFile

logger = logging.getLogger(__name__)


class FileEventHandlers(object):

    def __init__(self, prop):
        self.prop = prop

    def _get_history(self, target):
        return get_history(target, self.prop.attribute_name)

    @staticmethod
    def _remove_file(path):
        try:
            os.remove(path)
        except OSError, exc:
            if exc.errno==errno.ENOENT:
                logger.warning("Can't remove file %r: doesn't exist", path)
                #raise # XXX
            else:
                raise

    def _store_transient(self, target):
        transient = getattr(target, self.prop.key)
        if transient is None:
            for file_attr, target_attr in self.prop.cache_properties.items():
                setattr(target, target_attr, None)
            return
        if isinstance(transient, PersistentFile):
            return
        assert isinstance(transient, TransientFile), repr(transient)
        persistent = self._2persistent(target, transient)
        file_attr = getattr(type(target), self.prop.key)
        file_attr._states[target] = persistent

        for file_attr, target_attr in self.prop.cache_properties.items():
            setattr(target, target_attr, getattr(persistent, file_attr))

    def _2persistent(self, target, transient):
        session = object_session(target)
        persistent_name = getattr(target, self.prop.attribute_name)
        attr = getattr(type(target), self.prop.key)
        file_manager = session.find_file_manager(attr)
        persistent = file_manager.get_persistent(persistent_name,
                                                 self.prop.persistent_cls)

        file_attr = getattr(target.__class__, self.prop.key)
        file_manager = session.find_file_manager(file_attr)

        return file_manager.store(transient, persistent)

    def before_insert(self, mapper, connection, target):
        changes = self._get_history(target)
        if not changes:
            return
        self._store_transient(target)

    def before_update(self, mapper, connection, target):
        changes = self._get_history(target)
        if not (changes.deleted or changes.added):
            return
        if changes.deleted:
            old_name = self._get_file_name_to_delete(target, changes)
            if old_name:
                session = object_session(target)

                file_attr = getattr(target.__class__, self.prop.key)
                file_manager = session.find_file_manager(file_attr)

                old = file_manager.get_persistent(old_name,
                                                  self.prop.persistent_cls)
                self._remove_file(old.path)
        self._store_transient(target)

    def _get_file_name_to_delete(self, target, changes):
        if changes and changes.deleted:
            return changes.deleted[0]

    def after_delete(self, mapper, connection, target):
        changes = self._get_history(target)
        old_name = self._get_file_name_to_delete(target, changes)
        old_name = old_name or getattr(target, self.prop.attribute_name)
        if old_name is not None:
            session = object_session(target)

            file_attr = getattr(target.__class__, self.prop.key)
            file_manager = session.find_file_manager(file_attr)

            old = file_manager.get_persistent(old_name,
                                              self.prop.persistent_cls)
            self._remove_file(old.path)


class FileAttribute(object):

    def __init__(self, prop, class_=None):
        self.prop = prop
        self.column = prop.column
        self.attribute_name = prop.attribute_name
        self.name_template = prop.name_template
        self.class_ = class_
        self.cache_properties = prop.cache_properties
        self.persistent_cls = prop.persistent_cls
        # State for each instance
        self._states = WeakKeyDictionary()

    def __get__(self, inst, cls=None):
        if inst is None:
            return self
        if inst not in self._states:
            # XXX column name may differ from attribute name
            # empty string should be considered as None
            value = getattr(inst, self.attribute_name) or None
            if value is not None:
                session = object_session(inst)
                if session is None:
                    raise RuntimeError('Object is detached')
                if not hasattr(session, 'file_manager'):
                    raise RuntimeError(
                            "Session doesn't support file management")
                file_manager = session.find_file_manager(self)
                value = file_manager.get_persistent(value,
                                                    self.persistent_cls)

                for file_attr, target_attr in self.cache_properties.items():
                    setattr(value, file_attr, getattr(inst, target_attr))

            self._states[inst] = value
        return self._states[inst]

    def __set__(self, inst, value):
        if inst in self._states and self._states[inst]==value:
            return

        # sqlalchemy bug workaround
        # To get correct history we should assert that old value has been 
        # loaded from database. getattr loads lazy attribute.
        # See http://www.sqlalchemy.org/trac/ticket/2787
        old_name = getattr(inst, self.attribute_name)

        self._states[inst] = value
        if value is None:
            setattr(inst, self.attribute_name, None)
        elif isinstance(value, TransientFile):
            ext = os.path.splitext(value.name)[1]
            # XXX getting manager from a file object 
            #     looks like a hack
            name = value.manager.new_file_name(
                    self.name_template, inst, ext, old_name)
            setattr(inst, self.attribute_name, name)
        elif isinstance(value, PersistentFile):
            setattr(inst, self.attribute_name, value.name)
        else:
            raise ValueError('File property value must be TransientFile, '\
                             'PersistentFile or None')


class FileProperty(MapperProperty):

    attribute_cls = FileAttribute
    event_cls = FileEventHandlers

    def __init__(self, column, name_template, attribute_name=None, **options):
        self.column = column
        self._attribute_name = attribute_name
        self.name_template = name_template
        self._set_options(options)
        set_creation_order(self)

    @property
    def attribute_name(self):
        return self._attribute_name or self.column.key

    def _set_options(self, options):
        self.persistent_cls = options.pop('persistent_cls', PersistentFile)
        self.cache_properties = dict(options.pop('cache_properties', {}))
        assert not options, "Got unexpeted parameters: %s" % (
                options.keys())

    def instrument_class(self, mapper):
        handlers = self.event_cls(self)
        event.listen(mapper, 'before_insert', handlers.before_insert, propagate=True)
        event.listen(mapper, 'before_update', handlers.before_update, propagate=True)
        event.listen(mapper, 'after_delete', handlers.after_delete, propagate=True)
        setattr(mapper.class_, self.key, self.attribute_cls(self, mapper.class_))

    # XXX Implement merge?



def filesessionmaker(sessionmaker, file_manager, file_managers=None):
    u'''Wrapper of session maker adding link to a FileManager instance
    to session.::

        file_manager = FileManager(cfg.TRANSIENT_ROOT,
                                   cfg.PERSISTENT_ROOT)
        filesessionmaker(sessionmaker(...), file_manager)
    '''

    registry = WeakKeyDictionary()

    if file_managers:
        for k, v in file_managers.iteritems():
            registry[k] = v

    def find_file_manager(self, target):
        assert isinstance(target, FileAttribute)
        if target in registry:
            return registry[target]
        if hasattr(target, 'class_'):
            if target.class_ in registry:
                return registry[target.class_]
            if target.class_.metadata in registry:
                return registry[target.class_.metadata]
        return file_manager

    def session_maker(*args, **kwargs):
        session = sessionmaker(*args, **kwargs)
        # XXX in case we want to use session manager somehow bound 
        #     to request environment. For example, to generate user-specific
        #     URLs.
        #session.file_manager = \
        #        kwargs.get('file_manager', file_manager)
        session.file_manager = file_manager

        from types import MethodType

        session.find_file_manager = MethodType(find_file_manager,
                                               session, session.__class__)

        return session
    return session_maker
