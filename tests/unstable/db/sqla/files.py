import unittest, tempfile, shutil
from sqlalchemy import Column, Integer, orm, create_engine
from sqlalchemy.ext.declarative import declarative_base
from iktomi.db.sqla.declarative import AutoTableNameMeta
from iktomi.unstable.db.files import TransientFile, PersistentFile, \
                                     MediaFileManager, filesessionmaker


Base = declarative_base(metaclass=AutoTableNameMeta)


class ObjWithFile(Base):

    id = Column(Integer, primary_key=True)


class SqlaFilesTests(unittest.TestCase):

    def setUp(self):
        self.transient_root = tempfile.mkdtemp()
        self.persistent_root = tempfile.mkdtemp()
        self.media_file_manager = MediaFileManager(self.transient_root,
                                                   self.persistent_root)
        Session = filesessionmaker(orm.sessionmaker, self.media_file_manager)()
        engine = create_engine('sqlite://')
        Base.metadata.create_all(engine)
        self.db = Session(bind=engine)

    def tearDown(self):
        shutil.rmtree(self.transient_root)
        shutil.rmtree(self.persistent_root)

    def test_empty(self):
        obj = ObjWithFile()
        self.db.add(obj)
        self.db.commit()
