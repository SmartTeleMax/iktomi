import unittest, os, tempfile, shutil
from sqlalchemy import Column, Integer, VARBINARY, orm, create_engine
from sqlalchemy.ext.declarative import declarative_base
from iktomi.db.sqla.declarative import AutoTableNameMeta
from iktomi.unstable.db.files import TransientFile, PersistentFile, \
                                     FileManager
from iktomi.unstable.db.sqla.files import FileProperty, filesessionmaker


Base = declarative_base(metaclass=AutoTableNameMeta)


class ObjWithFile(Base):

    id = Column(Integer, primary_key=True)
    file_name = Column(VARBINARY(250))
    file = FileProperty(file_name, name_template='obj/{random}')
    file_by_id_name = Column(VARBINARY(250))
    file_by_id = FileProperty(file_by_id_name, name_template='obj/{item.id}')


class Subclass(ObjWithFile):

    __tablename__ = None


class SqlaFilesTests(unittest.TestCase):

    Model = ObjWithFile

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

    def test_session(self):
        self.assertTrue(hasattr(self.db, 'file_manager'))
        self.assertIsInstance(self.db.file_manager, FileManager)

    def test_create(self):
        obj = self.Model()
        obj.file = f = self.file_manager.new_transient()
        with open(f.path, 'wb') as fp:
            fp.write('test')
        self.assertIsInstance(obj.file, TransientFile)
        self.assertIsNotNone(obj.file_name)
        self.db.add(obj)
        self.db.commit()
        self.assertIsInstance(obj.file, PersistentFile)
        self.assertFalse(os.path.exists(f.path))
        self.assertTrue(os.path.isfile(obj.file.path))
        self.assertEqual(open(obj.file.path).read(), 'test')

    def test_update_none2file(self):
        obj = self.Model()
        self.db.add(obj)
        self.db.commit()
        obj.file = f = self.file_manager.new_transient()
        with open(f.path, 'wb') as fp:
            fp.write('test')
        self.assertIsInstance(obj.file, TransientFile)
        self.assertIsNotNone(obj.file_name)
        self.db.commit()
        self.assertIsInstance(obj.file, PersistentFile)
        self.assertFalse(os.path.exists(f.path))
        self.assertTrue(os.path.isfile(obj.file.path))
        self.assertEqual(open(obj.file.path).read(), 'test')

    def test_update_file2none(self):
        obj = self.Model()
        obj.file = f = self.file_manager.new_transient()
        with open(f.path, 'wb') as fp:
            fp.write('test')
        self.db.add(obj)
        self.db.commit()
        pf = obj.file

        obj.file = None
        self.assertIsNone(obj.file_name)
        self.assertTrue(os.path.exists(pf.path))
        self.db.commit()
        self.assertFalse(os.path.exists(pf.path))

    def test_update_file2file(self):
        obj = self.Model()
        obj.file = f = self.file_manager.new_transient()
        with open(f.path, 'wb') as fp:
            fp.write('test1')
        self.db.add(obj)
        self.db.commit()
        pf1 = obj.file

        obj.file = f = self.file_manager.new_transient()
        with open(f.path, 'wb') as fp:
            fp.write('test2')
        self.assertIsInstance(obj.file, TransientFile)
        self.assertIsNotNone(obj.file_name)
        self.db.commit()

        self.assertIsInstance(obj.file, PersistentFile)
        self.assertFalse(os.path.exists(f.path))
        self.assertFalse(os.path.exists(pf1.path))
        self.assertTrue(os.path.isfile(obj.file.path))
        self.assertEqual(open(obj.file.path).read(), 'test2')

    def test_update_file2self(self):
        obj = self.Model()
        obj.file = f = self.file_manager.new_transient()
        with open(f.path, 'wb') as fp:
            fp.write('test1')
        self.db.add(obj)
        self.db.commit()
        pf1 = obj.file

        obj.file = self.file_manager.get_persistent(obj.file.name)
        self.db.commit()

        self.assertIsInstance(obj.file, PersistentFile)
        self.assertTrue(os.path.exists(obj.file.path))
        self.assertEqual(pf1.path, obj.file.path)

    @unittest.skip('Not implemented')
    def test_update_file2file_not_random(self):
        obj = self.Model()

        obj.file_by_id = f = self.file_manager.new_transient()
        with open(f.path, 'wb') as fp:
            fp.write('test1')
        self.db.add(obj)
        self.db.commit()
        self.assertEqual(obj.file_by_id_name, 
                         self.Model.file_by_id.name_template.format(item=obj))
        pf1 = obj.file_by_id

        obj.file_by_id = f = self.file_manager.new_transient()
        with open(f.path, 'wb') as fp:
            fp.write('test2')
        self.assertIsInstance(obj.file_by_id, TransientFile)
        self.assertIsNotNone(obj.file_by_id_name)
        self.db.commit()

        self.assertIsInstance(obj.file_by_id, PersistentFile)
        self.assertFalse(os.path.exists(f.path))
        self.assertFalse(os.path.exists(pf1.path))
        self.assertTrue(os.path.isfile(obj.file_by_id.path))
        self.assertEqual(open(obj.file_by_id.path).read(), 'test2')

    @unittest.skip('Not implemented')
    def test_update_random_collision(self):
        obj = self.Model()
        self.db.add(obj)
        self.db.commit()

        obj.file = f = self.file_manager.new_transient()
        with open(f.path, 'wb') as fp:
            fp.write('test')

        persistent = self.file_manager.get_persistent(obj.file_name)
        dirname = os.path.dirname(persistent.path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        with open(persistent.path, 'wb') as fp:
            fp.write('taken')

        self.assertIsInstance(obj.file, TransientFile)
        self.assertIsNotNone(obj.file_name)
        self.db.commit()
        self.assertIsInstance(obj.file, PersistentFile)
        self.assertFalse(os.path.exists(f.path))
        self.assertTrue(os.path.isfile(obj.file.path))
        self.assertEqual(open(obj.file.path).read(), 'test')
        self.assertNotEqual(persistent.path, obj.file.path)
        self.assertEqual(open(persistent.path).read(), 'taken')

    def test_update_none2persistent(self):
        f = self.file_manager.get_persistent('persistent.txt')
        with open(f.path, 'wb') as fp:
            fp.write('test1')

        obj = self.Model()
        obj.file = f
        self.db.add(obj)
        self.db.commit()

        self.assertIsInstance(obj.file, PersistentFile)
        self.assertTrue(os.path.exists(obj.file.path))
        self.assertEqual(obj.file.name, 'persistent.txt')

    def test_delete(self):
        obj = self.Model()
        obj.file = f = self.file_manager.new_transient()
        with open(f.path, 'wb') as fp:
            fp.write('test')
        self.db.add(obj)
        self.db.commit()
        pf = obj.file
        self.db.delete(obj)
        self.db.commit()
        self.assertFalse(os.path.exists(pf.path))


class SqlaFilesTestsSubclass(SqlaFilesTests):

    Model = Subclass

