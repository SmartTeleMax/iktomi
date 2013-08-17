import os, logging
try:
    import Image
except ImportError:
    from PIL import Image
from sqlalchemy.orm.session import object_session
from iktomi.unstable.utils.image_resizers import ResizeFit
from ..files import TransientFile
from .files import FileEventHandlers, FileProperty

logger = logging.getLogger(__name__)


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
            image = self.prop.resize(image, self.prop.image_sizes)
            if self.prop.filter:
                if image.mode not in ['RGB', 'RGBA']:
                    image = image.convert('RGB')
                image = image.filter(self.filter)

            ext = os.path.splitext(persistent_name)[1]
            transient = session.file_manager.new_transient(ext)
            image.save(transient.path, quality=self.prop.quality)
            session.file_manager.store(transient, persistent_name)
            return persistent
        else:
            # Attention! This method can accept PersistentFile.
            # In this case one shold NEVER been deleted or rewritten.
            assert isinstance(transient, TransientFile), repr(transient)
            return FileEventHandlers._2persistent(self, target, transient)

    def before_update(self, mapper, connection, target):
        FileEventHandlers.before_update(self, mapper, connection, target)
        self._fill_img(mapper, connection, target)

    def before_insert(self, mapper, connection, target):
        FileEventHandlers.before_insert(self, mapper, connection, target)
        self._fill_img(mapper, connection, target)

    def _fill_img(self, mapper, connection, target):
        if self.prop.fill_from:
            # XXX Looks hacky
            value = getattr(target, self.prop.key)
            if value is None:
                base = getattr(target, self.prop.fill_from)
                if base is None:
                    return

                ext = os.path.splitext(base.name)[1]
                session = object_session(target)
                name = session.file_manager.new_file_name(
                        self.prop.name_template, target, ext, '')
                setattr(target, self.prop.column.key, name)

                persistent = self._2persistent(target, base)
                file_attr = getattr(type(target), self.prop.key)
                file_attr._states[target] = persistent


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

        assert self.fill_from is None or self.image_sizes is not None
        assert not options, "Got unexpeted parameters: %s" % (
                options.keys())

