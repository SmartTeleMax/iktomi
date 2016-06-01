import unittest, os, tempfile, shutil
from iktomi.db.files import TransientFile, PersistentFile, \
                                     FileManager, ReadonlyFileManager
from webob import Request
from io import BytesIO

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


class SqlaFilesTests(unittest.TestCase):

    def setUp(self):

        self.transient_root = tempfile.mkdtemp()
        self.persistent_root = tempfile.mkdtemp()
        self.transient_url = '/transient/'
        self.persistent_url = '/media/'

        self.file_manager = FileManager(self.transient_root,
                                        self.persistent_root,
                                        self.transient_url,
                                        self.persistent_url)

        self.ro_file_manager = ReadonlyFileManager(self.persistent_root,
                                                   self.persistent_url)

    def tearDown(self):
        shutil.rmtree(self.transient_root)
        shutil.rmtree(self.persistent_root)


    def test_file_attrs(self):
        with open(os.path.join(self.transient_root, 'testfile.html'), 'w') as f:
            f.write('<html></html>')

        fl = TransientFile(self.transient_root, 'testfile.html', self.file_manager)

        self.assertEqual(fl.mimetype, 'text/html')
        self.assertEqual(fl.size, 13)
        self.assertEqual(fl.file_name, 'testfile.html')
        self.assertEqual(fl.ext, '.html')
        self.assertEqual(fl.url, '/transient/testfile.html')

    def test_repr(self):
        with open(os.path.join(self.transient_root, 'testfile.html'), 'w') as f:
            f.write('<html></html>')

        fl = TransientFile(self.transient_root, 'testfile.html', self.file_manager)
        represent = repr(fl)
        self.assertIn('TransientFile', represent)
        self.assertIn('testfile.html', represent)

    def test_no_file(self):
        fl = PersistentFile(self.persistent_root, 'testfile2.html', self.file_manager)

        self.assertEqual(fl.mimetype, 'text/html')
        self.assertEqual(fl.size, None)
        self.assertEqual(fl.file_name, 'testfile2.html')
        self.assertEqual(fl.ext, '.html')
        self.assertEqual(fl.url, '/media/testfile2.html')

    def test_delete(self):
        with open(os.path.join(self.transient_root, 'delfile1.html'), 'w') as f:
            f.write('<html></html>')

        fl1 = TransientFile(self.transient_root, 'delfile1.html', self.file_manager)
        fl2 = TransientFile(self.transient_root, 'delfile2.html', self.file_manager)

        self.assertTrue(os.path.isfile(fl1.path))
        self.assertFalse(os.path.isfile(fl2.path))

        log = []
        with patch('logging.Logger.warning',
                   side_effect=lambda m: log.append(m)):
            self.file_manager.delete(fl1)
            self.file_manager.delete(fl2)

        self.assertFalse(os.path.isfile(fl1.path))
        self.assertFalse(os.path.isfile(fl2.path))
        self.assertIn('delfile2.html', log[0])
        self.assertIn('was not found', log[0])

    def test_delete_error(self):
        path = os.path.join(self.transient_root, 'delfile1.html')
        with open(path, 'w') as f:
            f.write('<html></html>')

        fl1 = TransientFile(self.transient_root, 'delfile1.html', self.file_manager)
        self.assertTrue(os.path.isfile(fl1.path))
        log = []

        # mocking permission error
        def unlink_error(path):
            raise OSError("[Errno 13] Permission denied: {}".format(path))

        with patch('logging.Logger.error',
                   side_effect=lambda m: log.append(m)):
            with patch('os.unlink', side_effect=unlink_error):
                with self.assertRaises(OSError) as exc:
                    self.file_manager.delete(fl1)

    def test_readonly_file_manager(self):
        get_persistent = self.ro_file_manager.get_persistent

        fl = get_persistent('name.txt')
        self.assertIsInstance(fl, PersistentFile)
        self.assertEqual(self.ro_file_manager.get_persistent_url(fl), '/media/name.txt')


        self.assertRaises(ValueError, get_persistent, 'something/../name.txt')
        self.assertRaises(ValueError, get_persistent, '/something/name.txt')
        self.assertRaises(ValueError, get_persistent, '~/something/name.txt')


    def test_create_transient(self):
        req_fl = os.path.join(self.transient_root, 'xxxxx.html')
        with open(req_fl, 'w') as f:
            f.write('<html></html>' * 10000)

        with open(req_fl) as f:
            request = Request.blank('/', POST={'file': ('big.html', f)})

            fl = self.file_manager.create_transient(request.POST['file'].file,
                                                    request.POST['file'].name)

        self.assertEqual(fl.size, 130000)

        # XXX this is a test of strange behaviour when browser does not
        #     pass Content-Length header when uploading a file in POST body
        #     See iktomi.cms.ajax_file_upload
        #     There is no obvious way to simulate this behaviour except
        #     hardcoded length variable.
        with open(req_fl, 'w') as f:
            f.write('<html></html>' * 10000)

        with open(req_fl) as f:
            request = Request.blank('/', POST={'file': ('big.html', f)})

            fl = self.file_manager.create_transient(request.POST['file'].file,
                                                    request.POST['file'].name,
                                                    length=130000)

        self.assertEqual(fl.size, 130000)

    def test_create_transient_dir(self):
        req_fl = os.path.join(self.transient_root, 'xxxxx.html')
        with open(req_fl, 'w') as f:
            f.write('<html></html>' * 10000)

        nonexistent_dir = os.path.join(self.transient_root,
                                       "non/existent/dir")

        self.assertFalse(os.path.exists(nonexistent_dir))

        self.file_manager.transient_root = nonexistent_dir

        with open(req_fl) as f:
            request = Request.blank('/', POST={'file': ('big.html', f)})
            fl = self.file_manager.create_transient(request.POST['file'].file,
                                                    request.POST['file'].name)

        self.assertEqual(fl.path, os.path.join(nonexistent_dir, fl.name))
        self.assertEqual(fl.size, 130000)

    def test_create_symlink(self):
        stream1 = BytesIO(b'hello')
        stream2 = BytesIO(b'world')

        source1 = self.file_manager.create_transient(stream1, 'hello.txt')
        source2 = self.file_manager.create_transient(stream2, 'world.txt')

        target_file_dir = os.path.join(self.persistent_root, 'dir/subdir')
        target_file = PersistentFile(target_file_dir, 'target.txt')
        target_file_path = os.path.join(target_file_dir, 'target.txt')
        self.assertFalse(os.path.isfile(target_file_path))

        self.file_manager.create_symlink(source1, target_file)

        self.assertTrue(os.path.isfile(target_file_path))

        with open(target_file_path) as f:
            self.assertEqual('hello', f.read())

        self.file_manager.create_symlink(source2, target_file)

        self.assertTrue(os.path.isfile(target_file_path))

        with open(target_file_path) as f:
            self.assertEqual('world', f.read())
