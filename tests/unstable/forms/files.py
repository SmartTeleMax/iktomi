import unittest, os, tempfile, shutil, cgi
from iktomi.unstable.db.files import TransientFile, FileManager
from iktomi.unstable.forms.files import FileFieldSet
from iktomi.forms import Form
from iktomi.web.app import AppEnvironment
from webob.multidict import MultiDict


class FormWithFile(Form):

    fields = [
        FileFieldSet('file'),
    ]


class FormFilesTests(unittest.TestCase):

    def setUp(self):
        self.transient_root = tempfile.mkdtemp()
        self.persistent_root = tempfile.mkdtemp()
        self.transient_url = '/transient/'
        self.persistent_url = '/media/'
        self.file_manager = FileManager(self.transient_root,
                                        self.persistent_root,
                                        self.transient_url,
                                        self.persistent_url)
        self.env = AppEnvironment.create(file_manager=self.file_manager)

    def tearDown(self):
        shutil.rmtree(self.transient_root)
        shutil.rmtree(self.persistent_root)

    def _create_persistent(self):
        f = self.file_manager.get_persistent('test.txt')
        with open(f.path, 'wb') as fp:
            fp.write('test')
        return f

    def _create_transient(self, content, original_name='test.txt'):
        f = self.file_manager.new_transient(ext=os.path.splitext(original_name)[1])
        with open(f.path, 'wb') as fp:
            fp.write(content)
        return f

    def _create_fs(self, mimetype, content, filename='uploaded.txt'):
        fs = cgi.FieldStorage()
        fs.file = fs.make_file()
        fs.type = mimetype
        fs.file.write(content)
        fs.file.seek(0)
        fs.filename = filename
        return fs

    def test_none2empty(self):
        form = FormWithFile(self.env)
        form.accept(MultiDict({'file.file': None,
                               'file.original_name': '',
                               'file.transient_name': '',
                               'file.mode': 'empty',}))
        data = form.python_data
        self.assertEqual(data['file'], None)

    def test_transient2empty(self):
        transient = self._create_transient('transient1')
        form = FormWithFile(self.env)
        form.accept(MultiDict({'file.file': None,
                               'file.original_name': 'test.txt',
                               'file.transient_name': transient.name,
                               'file.mode': 'transient',}))
        data = form.python_data
        self.assertIsInstance(data['file'], TransientFile)
        self.assertEqual(data['file'].name, transient.name)

    def test_transient_lost(self):
        form = FormWithFile(self.env)
        form.accept(MultiDict({'file.file': None,
                               'file.original_name': 'test.txt',
                               'file.transient_name': 'lost.txt',
                               'file.mode': 'transient',}))
        self.assertIn('file', form.errors)

    def test_transient_invalid(self):
        illegal = ['more/../../../lost.txt',
                   '../pass',
                   '/etc/pass',
                   '..',
                   '~',
                   ]
        for filename in illegal:
            form = FormWithFile(self.env)
            form.accept(MultiDict({'file.file': None,
                                   'file.original_name': 'test.txt',
                                   'file.transient_name': filename,
                                   'file.mode': 'transient',}))
            self.assertIn('file.transient_name', form.errors,
                          'file name is not filtered: %s' % filename)

    def test_file2empty(self):
        form = FormWithFile(self.env)
        fs = self._create_fs('text', 'file-content', 'filename.ttt')
        form.accept(MultiDict({'file.file': fs,
                               'file.mode': 'existing',}))
        data = form.python_data
        self.assertIsInstance(data['file'], TransientFile)
        self.assertEqual(os.path.splitext(data['file'].name)[1],
                         '.ttt')
        with open(data['file'].path) as fp:
            self.assertEqual(fp.read(), 'file-content')

    def test_none2persistent(self):
        persistent = self._create_persistent()
        form = FormWithFile(self.env, initial={'file': persistent})
        form.accept(MultiDict({'file.file': None,
                               'file.original_name': '',
                               'file.transient_name': '',
                               'file.mode': 'existing',}))
        data = form.python_data
        self.assertEqual(data['file'], persistent)

    def test_empty2persistent(self):
        persistent = self._create_persistent()
        form = FormWithFile(self.env, initial={'file': persistent})
        form.accept(MultiDict({'file.file': None,
                               'file.original_name': '',
                               'file.transient_name': '',
                               'file.mode': 'empty',}))
        data = form.python_data
        self.assertEqual(data['file'], None)

    def test_transient2persistent(self):
        persistent = self._create_persistent()
        transient = self._create_transient('transient1')
        form = FormWithFile(self.env, initial={'file': persistent})
        form.accept(MultiDict({'file.file': None,
                               'file.original_name': 'test.txt',
                               'file.transient_name': transient.name,
                               'file.mode': 'transient',}))
        data = form.python_data
        self.assertIsInstance(data['file'], TransientFile)
        self.assertEqual(data['file'].name, transient.name)

    def test_file2persistent(self):
        persistent = self._create_persistent()
        form = FormWithFile(self.env, initial={'file': persistent})
        fs = self._create_fs('text', 'file-content', 'filename.ttt')
        form.accept(MultiDict({'file.file': fs,
                               'file.mode': 'existing',}))
        data = form.python_data
        self.assertIsInstance(data['file'], TransientFile)
        self.assertEqual(os.path.splitext(data['file'].name)[1],
                         '.ttt')
        with open(data['file'].path) as fp:
            self.assertEqual(fp.read(), 'file-content')
