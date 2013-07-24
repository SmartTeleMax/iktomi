import unittest, tempfile, shutil
import Image
from PIL import ImageDraw
from sqlalchemy import Column, Integer, VARBINARY, orm, create_engine
from sqlalchemy.ext.declarative import declarative_base
from iktomi.db.sqla.declarative import AutoTableNameMeta
from iktomi.unstable.db.files import TransientFile, PersistentFile, \
                                     FileManager
from iktomi.unstable.db.sqla.files import filesessionmaker
from iktomi.unstable.db.sqla.images import ImageProperty


Base = declarative_base(metaclass=AutoTableNameMeta)


class ObjWithImage(Base):

    id = Column(Integer, primary_key=True)
    image_name = Column(VARBINARY(250))
    image = ImageProperty(image_name,
                          name_template='image/{0[random]}',
                          image_sizes=(200, 200))

    thumb_name = Column(VARBINARY(250))
    thumb = ImageProperty(thumb_name,
                          name_template='thumb/{0[random]}',
                          image_sizes=(100, 100),
                          fill_from='image')

    icon_name = Column(VARBINARY(250))
    icon = ImageProperty(icon_name,
                         name_template='icon/{0[random]}')



def _create_image(path, width=400, height=400):
    image = Image.new('RGB', (width, height), (124,
                                               124,
                                               124, 1))
    #from random import randint
    #image = Image.new('RGB', (width, height), (randint(1, 240),
    #                                           randint(1, 240),
    #                                           randint(1, 240), 1))
    #for x in xrange(0, randint(1, 5)):
    #    draw = ImageDraw.Draw(image)
    #    points = [(randint(1, width), randint(1, height))
    #              for x in xrange(0, randint(4, 6))]
    #    draw.polygon(points, fill=(randint(150, 255),
    #                               randint(150, 255),
    #                               randint(150, 255), 1))
    image.save(path)


class SqlaImagesTests(unittest.TestCase):

    def setUp(self):
        self.transient_root = tempfile.mkdtemp()
        self.persistent_root = tempfile.mkdtemp()
        self.transient_url = '/transient/'
        self.persistent_url = '/media/'
        self.file_manager = FileManager(self.transient_root,
                                        self.persistent_root,
                                        self.transient_url,
                                        self.persistent_url)
        Session = filesessionmaker(orm.sessionmaker(), self.file_manager)
        engine = create_engine('sqlite://')
        Base.metadata.create_all(engine)
        self.db = Session(bind=engine)

    def tearDown(self):
        shutil.rmtree(self.transient_root)
        shutil.rmtree(self.persistent_root)

    def test_create(self):
        obj = ObjWithImage()
        obj.image = f = self.file_manager.new_transient('.gif')
        _create_image(f.path)
        self.db.add(obj)
        self.db.commit()

        self.assertIsInstance(obj.image, PersistentFile)
        self.assertIsInstance(obj.thumb, PersistentFile)

        img = Image.open(obj.image.path)
        self.assertEqual(img.size, (200, 200))

        thumb = Image.open(obj.thumb.path)
        self.assertEqual(thumb.size, (100, 100))

    def test_no_size(self):
        obj = ObjWithImage()
        obj.icon = f = self.file_manager.new_transient('.gif')
        _create_image(f.path, 200, 300)
        self.db.add(obj)
        self.db.commit()

        self.assertIsNone(obj.image)
        self.assertIsNone(obj.thumb)
        self.assertIsInstance(obj.icon, PersistentFile)

        img = Image.open(obj.icon.path)
        self.assertEqual(img.size, (200, 300))

    def test_no_img(self):
        obj = ObjWithImage()
        self.db.add(obj)
        self.db.commit()

        self.assertEqual(obj.image, None)
        self.assertEqual(obj.thumb, None)
        self.assertEqual(obj.icon, None)

    def test_update(self):
        obj = ObjWithImage()
        self.db.add(obj)
        self.db.commit()

        obj.image = f = self.file_manager.new_transient('.gif')
        _create_image(f.path)
        self.db.commit()

        self.assertIsInstance(obj.image, PersistentFile)
        self.assertIsInstance(obj.thumb, PersistentFile)

        img = Image.open(obj.image.path)
        self.assertEqual(img.size, (200, 200))

        thumb = Image.open(obj.thumb.path)
        self.assertEqual(thumb.size, (100, 100))

    def test_invalid(self):
        obj = ObjWithImage()
        obj.image = f = self.file_manager.new_transient('.gif')
        with open(f.path, 'wb') as fp:
            fp.write('test')
        self.db.add(obj)
        with self.assertRaises(IOError):
            self.db.commit()

    def test_fill_without_size(self):
        with self.assertRaises(AssertionError):
            class Test(Base):

                id = Column(Integer, primary_key=True)
                image_name = Column(VARBINARY(250))
                image = ImageProperty(image_name,
                                      name_template='image/{0[random]}')

                thumb_name = Column(VARBINARY(250))
                thumb = ImageProperty(thumb_name,
                                      name_template='thumb/{0[random]}',
                                      fill_from='image')

