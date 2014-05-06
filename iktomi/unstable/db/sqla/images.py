import os, logging
try:
    import Image
except ImportError:       # pragma: no cover
    from PIL import Image # pragma: no cover
from sqlalchemy.orm.session import object_session
from iktomi.unstable.utils.image_resizers import ResizeFit
from iktomi.utils import cached_property
from ..files import TransientFile, PersistentFile
from .files import FileEventHandlers, FileProperty

logger = logging.getLogger(__name__)


class ImageFile(PersistentFile):

    def _get_properties(self, properties=['width', 'height']):
        if 'width' in properties or 'height' in properties:
            image = Image.open(self.path)
            self.width, self.height = image.size

    @cached_property
    def width(self):
        self._get_properties(['width'])
        return self.width

    @cached_property
    def height(self):
        self._get_properties(['height'])
        return self.height


class ImageEventHandlers(FileEventHandlers):

    def _2persistent(self, target, transient):
        # XXX move this method to file_manager

        # XXX Do this check or not?
        image = Image.open(transient.path)
        assert image.format in Image.SAVE and image.format != 'bmp',\
                'Unsupported image format'

        if self.prop.image_sizes:
            session = object_session(target)
            persistent_name = getattr(target, self.prop.attribute_name)
            ext = os.path.splitext(persistent_name)[1]
            if not ext:
                ext = '.' + image.format.lower()
                # set extension if it is not set
                # XXX hack?
                persistent_name += ext
                setattr(target, self.prop.attribute_name, persistent_name)

            image_attr = getattr(target.__class__, self.prop.key)
            file_manager = persistent = session.find_file_manager(image_attr)
            persistent = file_manager.get_persistent(persistent_name,
                                                     self.prop.persistent_cls)

            image = self.prop.resize(image, self.prop.image_sizes)
            if self.prop.enhancements:
                if image.mode not in ['RGB', 'RGBA']:
                    image = image.convert('RGB')
                for enhance, factor in self.prop.enhancements:
                    image = enhance(image).enhance(factor)

            if self.prop.filter:
                if image.mode not in ['RGB', 'RGBA']:
                    image = image.convert('RGB')
                image = image.filter(self.prop.filter)

            transient = session.find_file_manager(image_attr).new_transient(ext)
            image.save(transient.path, quality=self.prop.quality)
            session.find_file_manager(image_attr).store(transient, persistent)
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
                image_attr = getattr(target.__class__, self.prop.key)
                name = session.find_file_manager(image_attr).new_file_name(
                        self.prop.name_template, target, ext, '')
                setattr(target, self.prop.attribute_name, name)

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
        self.filter = options.pop('filter', None)
        self.enhancements = options.pop('enhancements', [])
        self.quality = options.pop('quality', 85)

        assert self.fill_from is None or self.image_sizes is not None

        options.setdefault('persistent_cls', ImageFile)
        FileProperty._set_options(self, options)

