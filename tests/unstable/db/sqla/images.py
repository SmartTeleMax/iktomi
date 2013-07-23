import unittest, tempfile, shutil
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
                          name_template='image/{0[random]}')

    thumb_name = Column(VARBINARY(250))
    thumb = ImageProperty(thumb_name,
                          name_template='thumb/{0[random]}',
                          image_sizes=(100, 100),
                          fill_from='image')


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

    #def test_image(self):
    #    obj = ObjWithImage()

    #def test_invalid(self):
    #    obj = ObjWithImage()

    #def test_fill(self):
    #    obj = ObjWithImage()

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


