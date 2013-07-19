import os, errno, logging
import Image
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.interfaces import MapperProperty
from sqlalchemy.orm.attributes import get_history
from sqlalchemy import event
from sqlalchemy.util import set_creation_order
from weakref import WeakKeyDictionary
from ..files import TransientFile, PersistentFile
from iktomi.unstable.utils.image_resizers import ResizeFit

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
                raise # XXX
            else:
                raise

    def _store_transient(self, target):
        transient = getattr(target, self.prop.key)
        if transient is None:
            return
        assert isinstance(transient, TransientFile)
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
            old_name = changes.deleted[0]
            if old_name is not None:
                session = object_session(target)
                old = session.file_manager.get_persistent(old_name)
                self._remove_file(old.path)
        self._store_transient(target)

    def after_delete(self, mapper, connection, target):
        changes = self._get_history(target)
        if changes and changes.deleted:
            old_name = changes.deleted[0]
        else:
            old_name = getattr(target, self.prop.column.key)
        if old_name is not None:
            session = object_session(target)
            old = session.file_manager.get_persistent(old_name)
            self._remove_file(old.path)


class ImageEventHandlers(FileEventHandlers):

    def _2persistent(self, target, transient):
        # XXX move this method to file_manager

        # XXX Do this check or not?
        image = Image.open(transient.path)
        assert image.format in Image.SAVE and image.format != 'bmp',\
                'Unsupported image format'

        if self.prop.image_sizes:
            session = object_session(target)
            persistent_name = getattr(target, self.prop.column.key)
            persistent = session.file_manager.get_persistent(persistent_name)
            image = self.resize(image, self.image_sizes)
            if self.prop.filter:
                if image.mode not in ['RGB', 'RGBA']:
                    image = image.convert('RGB')
                image = image.filter(self.filter)

            image.save(persistent.path, quality=self.prop.quality)
            return persistent
        else:
            # Attention! This method can accept PersistentFile.
            # In this case one shold NEVER been deleted or rewritten.
            assert isinstance(transient, TransientFile)
            return FileEventHandlers._2persistent(self, target, transient)

    def before_update(self, mapper, connection, target):
        # XXX Looks hacky
        FileEventHandlers.before_update(self, mapper, connection, target)
        if self.prop.fill_from:
            value = getattr(target, self.prop.key)
            if value is None:
                base = getattr(target, self.prop.fill_from)
                persistent = self._2persistent(self, target, base)
                file_attr = getattr(type(target), self.prop.key)
                file_attr._states[target] = persistent


class _AttrDict(object):

    def __init__(self, inst):
        self.__inst = inst

    def __getitem__(self, key):
        if key == 'random':
            # XXX invent better way to include random strings
            return os.urandom(8).encode('hex')
        return getattr(self.__inst, key)


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

    def new_file_name(self, inst, ext):
        # XXX Must differ from old value[s]. How to add support for random,
        # sequence?
        name = self.name_template.format(_AttrDict(inst))
        return name + ext

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
            name = self.new_file_name(inst, ext)
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


class ImageProperty(FileProperty):

    event_cls = ImageEventHandlers

    def _set_options(self, options):
        # XXX rename image_sizes?
        options = dict(options)
        self.image_sizes = options.pop('image_sizes', None)
        self.resize = options.pop('resize', None) or ResizeFit()
        # XXX implement
        self.fill_from = options.pop('fill_from', None)
        self.filter = options.pop('fillter', None)
        self.quality = options.pop('quality', 85)

        assert self.fill_from is None or self.image_sizes is None
        assert not options, "Got unexpeted parameters: %s" % (
                options.keys())


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
