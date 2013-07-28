import os, errno, logging
import Image
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
        return get_history(target, self.prop.column.key)

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
            return
        assert isinstance(transient, TransientFile), repr(transient)
        persistent = self._2persistent(target, transient)
        file_attr = getattr(type(target), self.prop.key)
        file_attr._states[target] = persistent

    def _2persistent(self, target, transient):
        session = object_session(target)
        persistent_name = getattr(target, self.prop.column.key)
        return session.file_manager.store(transient, persistent_name)

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
            if old_name is not None:
                session = object_session(target)
                old = session.file_manager.get_persistent(old_name)
                self._remove_file(old.path)
        self._store_transient(target)

    def _get_file_name_to_delete(self, target, changes):
        if changes and changes.deleted:
            return changes.deleted[0]

    def after_delete(self, mapper, connection, target):
        changes = self._get_history(target)
        old_name = self._get_file_name_to_delete(target, changes)
        old_name = old_name or getattr(target, self.prop.column.key)
        if old_name is not None:
            session = object_session(target)
            old = session.file_manager.get_persistent(old_name)
            self._remove_file(old.path)


class FileAttribute(object):

    def __init__(self, prop):
        self.column = prop.column
        self.name_template = prop.name_template
        # State for each instance
        self._states = WeakKeyDictionary()

    def __get__(self, inst, cls=None):
        if inst is None:
            return self
        if inst not in self._states:
            # XXX column name may differ from attribute name
            # empty string should be considered as None
            value = getattr(inst, self.column.key) or None
            if value is not None:
                session = object_session(inst)
                if session is None:
                    raise RuntimeError('Object is detached')
                if not hasattr(session, 'file_manager'):
                    raise RuntimeError(
                            "Session doesn't support file management")
                value = session.file_manager.get_persistent(value)
            self._states[inst] = value
        return self._states[inst]

    def __set__(self, inst, value):
        if inst in self._states and self._states[inst]==value:
            return

        # sqlalchemy bug workaround
        # To get correct history we should assert that old value has been 
        # loaded from database. getattr loads lazy attribute.
        # See http://www.sqlalchemy.org/trac/ticket/2787
        getattr(inst, self.column.key)

        self._states[inst] = value
        if value is None:
            setattr(inst, self.column.key, None)
        elif isinstance(value, TransientFile):
            ext = os.path.splitext(value.name)[1]
            # XXX getting manager from a file object 
            #     looks like a hack
            name = value.manager.new_file_name(
                    self.name_template, inst, ext)
            setattr(inst, self.column.key, name)
        elif isinstance(value, PersistentFile):
            setattr(inst, self.column.key, value.name)
        else:
            raise ValueError('File property value must be TransientFile, '\
                             'PersistentFile or None')


class FileProperty(MapperProperty):

    attribute_cls = FileAttribute
    event_cls = FileEventHandlers

    def __init__(self, column, name_template, **options):
        self.column = column
        self.name_template = name_template
        self._set_options(options)
        set_creation_order(self)

    def _set_options(self, options):
        assert not options, 'FileProperty accepts no options'

    def instrument_class(self, mapper):
        handlers = self.event_cls(self)
        event.listen(mapper, 'before_insert', handlers.before_insert)
        event.listen(mapper, 'before_update', handlers.before_update)
        event.listen(mapper, 'after_delete', handlers.after_delete)
        setattr(mapper.class_, self.key, self.attribute_cls(self))

    # XXX Implement merge?



def filesessionmaker(sessionmaker, file_manager):
    u'''Wrapper of session maker adding link to a FileManager instance
    to session.::

        file_manager = FileManager(cfg.TRANSIENT_ROOT,
                                   cfg.PERSISTENT_ROOT)
        filesessionmaker(sessionmaker(...), file_manager)
    '''
    def session_maker(*args, **kwargs):
        session = sessionmaker(*args, **kwargs)
        # XXX in case we want to use session manager somehow bound 
        #     to request environment. For example, to generate user-specific
        #     URLs.
        #session.file_manager = \
        #        kwargs.get('file_manager', file_manager)
        session.file_manager = file_manager
        return session
    return session_maker
