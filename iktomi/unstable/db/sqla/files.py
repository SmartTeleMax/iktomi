import os
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.types import VARBINARY, TypeDecorator
from sqlalchemy.orm.session import object_session
from sqlalchemy import event
from weakref import WeakKeyDictionary
from ..files import TransientFile, PersistentFile


class FileEventHandlers(object):

    def __init__(self, key):
        self.key = key

    def before_insert(self, mapper, connection, target):
        print 'before_insert'

    def before_update(self, mapper, connection, target):
        print 'before_update'

    def after_delete(self, mapper, connection, target):
        print 'after_delete'


class _AttrDict(object):

    def __init__(self, inst):
        self.__inst = inst

    def __getitem__(self, key):
        return getattr(self.__inst, key)


class FileProperty(object):

    def __init__(self, column, name_template):
        self.column = column
        self.name_template = name_template
        # State for each instance
        self._states = WeakKeyDictionary()

    def listen(self, mapper):
        handlers = FileEventHandlers(self.key)
        event.listen(mapper, 'before_insert', handlers.before_insert)
        event.listen(mapper, 'before_update', handlers.before_update)
        event.listen(mapper, 'after_delete', handlers.after_delete)

    def __get__(self, inst, cls=None):
        if inst is None:
            return self
        if inst not in self._states:
            value = getattr(inst, self.column.key)
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

    def new_file_name(self, inst, ext):
        # XXX Must differ from old value[s]. How to add support for random,
        # sequence?
        name = self.name_template.format(_AttrDict(inst))
        return name + ext

    def __set__(self, inst, value):
        if inst in self._states and self._states[inst]==value:
            return
        self._states[inst] = value
        if value is None:
            setattr(inst, self.column.key, None)
        elif isinstance(value, TransientFile):
            ext = os.path.splitext(value.name)[1]
            name = self.new_file_name(inst, ext)
            setattr(inst, self.column.key, name)
        elif isinstance(value, PersistentFile):
            setattr(inst, self.column.key, value.name)
        else:
            raise ValueError('File property value must be TransientFile, '\
                             'PersistentFile or None')
