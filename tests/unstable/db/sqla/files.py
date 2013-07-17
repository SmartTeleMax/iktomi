import unittest, tempfile, shutil
from sqlalchemy import Column, Integer, VARBINARY, orm, create_engine
from sqlalchemy.ext.declarative import declarative_base
from iktomi.db.sqla.declarative import AutoTableNameMeta
from iktomi.unstable.db.files import TransientFile, PersistentFile, \
                                     FileManager, filesessionmaker
from iktomi.unstable.db.sqla.files import FileProperty


Base = declarative_base(metaclass=AutoTableNameMeta)


class ObjWithFile(Base):

    id = Column(Integer, primary_key=True)
    file_name = Column(VARBINARY(250), nullable=False)
    #file = FileProperty(file_name, name_template='obj/{id}')
    file = FileProperty(file_name, name_template='obj')


class SqlaFilesTests(unittest.TestCase):

    def setUp(self):
        self.transient_root = tempfile.mkdtemp()
        self.persistent_root = tempfile.mkdtemp()
        self.file_manager = FileManager(self.transient_root,
                                        self.persistent_root)
        Session = filesessionmaker(orm.sessionmaker, self.file_manager)()
        engine = create_engine('sqlite://')
        Base.metadata.create_all(engine)
        self.db = Session(bind=engine)

    def tearDown(self):
        shutil.rmtree(self.transient_root)
        shutil.rmtree(self.persistent_root)

    def test_create(self):
        obj = ObjWithFile()
        obj.file = f = self.file_manager.new_transient()
        self.assertIsInstance(obj.file, TransientFile)
        self.assertIsNotNone(obj.file_name)
        self.db.add(obj)
        self.db.commit()
        self.assertIsInstance(obj.file, PersistentFile)
        # XXX

    def test_update_none2file(self):
        pass # XXX

    def test_update_file2none(self):
        pass # XXX

    def test_update_file2file(self):
        pass # XXX

    def test_delete(self):
        pass # XXX
