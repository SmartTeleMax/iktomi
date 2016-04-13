import unittest, os, tempfile, shutil
from iktomi.unstable.db.files import TransientFile, PersistentFile, \
                                     FileManager
from webob import Request


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

    def test_no_file(self):
        fl = PersistentFile(self.persistent_root, 'testfile2.html', self.file_manager)

        self.assertEqual(fl.mimetype, 'text/html')
        self.assertEqual(fl.size, None)
        self.assertEqual(fl.file_name, 'testfile2.html')
        self.assertEqual(fl.ext, '.html')
        self.assertEqual(fl.url, '/media/testfile2.html')

    def test_delete(self):
        # XXX how to test lack of permissions?
        with open(os.path.join(self.transient_root, 'testfile1.html'), 'w') as f:
            f.write('<html></html>')

        fl1 = TransientFile(self.transient_root, 'testfile1.html', self.file_manager)
        fl2 = TransientFile(self.transient_root, 'testfile2.html', self.file_manager)

        assert os.path.isfile(fl1.path)
        assert not os.path.isfile(fl2.path)

        self.file_manager.delete(fl1)
        self.file_manager.delete(fl2)

        assert not os.path.isfile(fl1.path)
        assert not os.path.isfile(fl2.path)

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
