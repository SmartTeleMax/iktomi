# -*- coding: utf-8 -*-
import unittest
import os
from copy import copy

from insanities.forms import fields, convs, form, widgets, media, perms
from insanities.web import Map

from insanities.ext.jinja2 import JinjaEnv, FormEnvironment
from insanities.ext.gettext import LanguageSupport, set_lang, FormEnvironmentMixin


class TranslationFormEnv(FormEnvironment, FormEnvironmentMixin): pass

class Config(object): pass



class TranslationTestCase(unittest.TestCase):
    def setUp(self):
        pass
    
    def get_app(self, chains=[], languages=['en', 'ru']):
        app = Map(
            LanguageSupport(languages, os.path.join(CURDIR, 'mo')),
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
        self.assertEqual(rctx.translation.language, 'en')
    
    def test_set_lang(self):
        pass
    
    def test_translation(self):
        pass
    
    def test_ntranslation(self):
        pass
    
    def test_translation_forms(self):
        pass

    def test_translation_forms_multiple(self):
        pass

    def test_translation_forms_templates(self):
        pass

    def test_translation_templates(self):
        pass
    
    def test_make(self):
        pass
    
    def test_compile(self):
        pass
    
    
CURDIR = os.path.dirname(os.path.abspath(__file__))
    
if __name__ == '__main__':
    unittest.main()
