import unittest
from iktomi.unstable.db.sqla.factories import ModelFactories, LangModelProxy, \
        ModelsProxy, PseudoModel

class _ModuleMock():

    def __init__(self, name):
        self.__name__ = name

    def __repr__(self):
        return self.__name__


class Tests(unittest.TestCase):

    def test_make_class(self):
        reg = ModelFactories()

        @reg.register()
        def A(models):
            a = 2

        @reg.register('A')
        def B(models):
            b = 1
            a = models.A.a

        self.assertEqual(len(reg.models), 2)
        self.assertEqual(len(reg.i18n_models), 0)

        module = _ModuleMock('xmodule')

        reg.create_all(module)

        self.assertIsInstance(module.A, type)
        self.assertIsInstance(module.B, type)
        assert issubclass(module.B, module.A)

        self.assertIs(module.B.models, module)
        self.assertEqual(module.B.__module__, 'xmodule')
        self.assertEqual(module.B.__name__, 'B')
        self.assertEqual(module.B.b, 1)
        self.assertEqual(module.B.a, 2)


    def test_make_lang_class(self):
        reg = ModelFactories()
        langs = ['en', 'ru']

        @reg.register(langs=langs, lang=True)
        def A(models):
            pass

        @reg.register('A', langs=langs, lang=True)
        def B(models):
            A = models.A


        self.assertEqual(len(reg.models), 0)
        self.assertEqual(len(reg.i18n_models), 2)

        module = _ModuleMock('xmodule')
        module.ru = LangModelProxy(module, langs, 'ru')
        module.en = LangModelProxy(module, langs, 'en')

        reg.create_all(module)

        assert not hasattr(module, 'A')
        assert not hasattr(module, 'B')

        self.assertIs(module.ru.A, module.ARu)
        self.assertIs(module.ru.B, module.BRu)
        self.assertIs(module.ru.B.models, module.ru)
        self.assertEqual(module.ru.B.models.lang, 'ru')
        self.assertIs(module.ru.B.A, module.ARu)

        self.assertEqual(module.en.main_lang, 'en')
        self.assertEqual(module.ru.main_lang, 'en')

        assert issubclass(module.BRu, module.ARu)

    def test_make_mixed_classes(self):
        reg = ModelFactories()
        langs = ['en', 'ru']

        @reg.register()
        def A(models):
            pass

        @reg.register('A', langs=langs, lang=True)
        def B(models):
            A = models.A


        self.assertEqual(len(reg.models), 1)
        self.assertEqual(len(reg.i18n_models), 1)

        module = _ModuleMock('xmodule')
        module.ru = LangModelProxy(module, langs, 'ru')
        module.en = LangModelProxy(module, langs, 'en')

        reg.create_all(module)

        assert not hasattr(module, 'ARu')
        assert not hasattr(module, 'AEn')
        assert not hasattr(module, 'B')

        self.assertIs(module.ru.A, module.A)
        self.assertIs(module.ru.B, module.BRu)
        self.assertIs(module.ru.B.models, module.ru)

        assert issubclass(module.BRu, module.A)

    def test_create_by_name(self):
        reg = ModelFactories()
        langs = ['en', 'ru']

        @reg.register()
        def A(models):
            pass

        @reg.register()
        def B(models):
            pass

        @reg.register(langs=langs, lang=True)
        def C(models):
            pass

        @reg.register(langs=langs, lang=True)
        def D(models):
            pass

        module = _ModuleMock('xmodule')
        module.ru = LangModelProxy(module, langs, 'ru')
        module.en = LangModelProxy(module, langs, 'en')

        reg.create_all(module, model_names=['A', 'C'])

        assert not hasattr(module, 'B')
        assert not hasattr(module, 'C')
        assert not hasattr(module, 'DRu')
        assert not hasattr(module, 'DEn')
        self.assertIsInstance(module.A, type)
        self.assertIsInstance(module.CRu, type)
        self.assertIsInstance(module.CEn, type)

    def test_create_by_lang(self):
        reg = ModelFactories()
        langs = ['en', 'ru']

        @reg.register()
        def A(models):
            pass

        @reg.register(langs=['ru'], lang=True)
        def B(models):
            pass

        @reg.register(lang=True)
        def C(models):
            pass

        module = _ModuleMock('xmodule')
        module.ru = LangModelProxy(module, langs, 'ru')
        module.en = LangModelProxy(module, langs, 'en')

        reg.create_all(module, all_lang_modules=[module.ru, module.en])

        assert not hasattr(module, 'B')
        assert not hasattr(module, 'BEn')
        assert not hasattr(module.en, 'B')
        self.assertIsInstance(module.A, type)
        self.assertIsInstance(module.BRu, type)
        self.assertIsInstance(module.ru.B, type)
        self.assertIsInstance(module.CRu, type)
        self.assertIsInstance(module.CEn, type)

    def test_no_override(self):
        reg = ModelFactories()
        langs = ['en', 'ru']

        @reg.register()
        def A(models):
            pass

        @reg.register(lang=True)
        def B(models):
            pass

        module = _ModuleMock('xmodule')
        module.ru = LangModelProxy(module, langs, 'ru')
        module.en = LangModelProxy(module, langs, 'en')
        module.A = 'EXISTS'
        module.BRu = 'EXISTS'

        reg.create_all(module, all_lang_modules=[module.ru, module.en])

        self.assertEqual(module.A, 'EXISTS')
        self.assertEqual(module.BRu, 'EXISTS')

    def test_model_proxy(self):
        reg = ModelFactories()
        langs = ['en', 'ru']

        @reg.register()
        def A(models):
            b = models.B
            self.assertIsInstance(models.B, PseudoModel)
            self.assertEqual(str(models.B), 'B')
            self.assertEqual(str(models.B.c), 'B.c')
            self.assertRaises(AttributeError, lambda: models.C)

        @reg.register()
        def B(models):
            pass

        @reg.register(lang=True)
        def C(models):
            self.assertEqual(str(models.C), 'C'+models.lang.title())

        module = _ModuleMock('xmodule')
        module.ru = LangModelProxy(module, langs, 'ru')
        module.en = LangModelProxy(module, langs, 'en')

        reg.create_all(module, all_lang_modules=[module.ru, module.en])

        self.assertIsInstance(module.A.b, PseudoModel) # XXX

