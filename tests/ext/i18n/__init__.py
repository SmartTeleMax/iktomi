# -*- coding: utf-8 -*-
import unittest
import os
from copy import copy
import shutil

from insanities.forms import fields, convs, form, widgets, media, perms
from insanities.web import Map

from insanities.ext.jinja2 import JinjaEnv, FormEnvironment
from insanities.ext.gettext import LanguageSupport, set_lang, FormEnvironmentMixin
from insanities.ext.gettext.commands import gettext_commands
import insanities

from gettext import GNUTranslations


class TranslationFormEnv(FormEnvironment, FormEnvironmentMixin): pass

INSANITIES_ROOT = CURDIR = os.path.dirname(os.path.abspath(insanities.__file__))
CURDIR = os.path.dirname(os.path.abspath(__file__))

class Config(object):
    LOCALE_FILES = [
        os.path.join(INSANITIES_ROOT, 'locale/%s/LC_MESSAGES/insanities-core.po'),
        os.path.join(CURDIR, 'locale/%s/LC_MESSAGES/test.po'),
    ]
    pass



class TranslationTestCase(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        modir = os.path.join(CURDIR, 'mo')
        if os.path.isdir(modir):
            shutil.rmtree(modir)
    
    def get_app(self, chains=[], languages=['en', 'ru']):
        app = Map(
            LanguageSupport(languages, os.path.join(CURDIR, 'locale')),
            JinjaEnv(paths=[os.path.join(CURDIR, 'templates')],
                     EnvCls=TranslationFormEnv),
            *chains)
        
        return app
    
    def run_app(self, app, env={}):
        rctx = app.rctx_class(env, app.url_for)
        #rctx.response.status = httplib.NOT_FOUND
        return app(rctx)

    def test_language_support(self):
        app = self.get_app(languages=['en', 'ru'])
        rctx = self.run_app(app)
        self.assertEqual(rctx.languages, ['en', 'ru'])
        self.assertEqual(rctx.language, 'en')
        assert isinstance(rctx.translation, GNUTranslations)
        #self.assertEqual(rctx.translation.plural, 'en')
    
    def test_set_lang(self):
        app = self.get_app(languages=['en', 'ru'], chains=[
                set_lang('ru'),
            ])
        rctx = self.run_app(app)
        self.assertEqual(rctx.languages, ['en', 'ru'])
        self.assertEqual(rctx.language, 'ru')
        assert isinstance(rctx.translation, GNUTranslations)
    
    def test_ntranslation(self):
        raise NotImplementedError()
    
    def test_translation_forms(self):
        raise NotImplementedError()

    def test_translation_forms_multiple(self):
        raise NotImplementedError()

    def test_translation_forms_templates(self):
        raise NotImplementedError()

    def test_translation_templates(self):
        raise NotImplementedError()
    
    def test_make(self):
        class Config(object):
            pass
        command = gettext_commands(Config())
        raise NotImplementedError()
    
    def test_compile(self):
        class Config(object):
            LOCALE_FILES = [
                os.path.join(CURDIR, 'locale/%s/LC_MESSAGES/test.po'),
                os.path.join(INSANITIES_ROOT, 'locale/%s/LC_MESSAGES/insanities-core.po'),
            ]
        command = gettext_commands(Config())
        command.command_compile(locale='ru',
                                localedir=os.path.join(CURDIR, 'mo'),
                                dbg=True, domain='test')
        
        outfile_dbg = os.path.join(CURDIR, 'mo/ru/LC_MESSAGES/_dbg.po')
        with open(outfile_dbg) as pofile:
            string = pofile.read().decode('utf-8')
            assert 'Plural-Forms:' in string
            assert u"временный файл v2" in string
            assert u"специальныйтестовыймессидж" in string
            assert u"удалить" in string


if __name__ == '__main__':
    unittest.main()
