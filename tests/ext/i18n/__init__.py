# -*- coding: utf-8 -*-
import unittest
import os
from copy import copy
import shutil

from insanities.forms import fields, convs, form, widgets, media, perms
from insanities.web import Map
from insanities.web.http import Request, RequestContext

from insanities.ext.jinja2 import jinja_env, FormEnvironment
from insanities.ext.gettext import LanguageSupport, set_lang, gettext_commands
from insanities.utils.i18n import N_, M_
import insanities

from gettext import GNUTranslations

import logging
logger = logging.getLogger(__name__)


INSANITIES_ROOT = CURDIR = os.path.dirname(os.path.abspath(insanities.__file__))
CURDIR = os.path.dirname(os.path.abspath(__file__))

EN_SINGLE = "The length should be at least one symbol"
EN_PLURAL = "The length should be at least %(min_length)s symbols"
RU_PLURAL_1 = u"Длина должна быть не менее %s символов"

class TranslationTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        modir = os.path.join(CURDIR, 'mo')
        if os.path.isdir(modir):
            shutil.rmtree(modir)

    def get_app(self, chains=[], languages=['en', 'ru']):
        app = LanguageSupport(languages, os.path.join(CURDIR, 'locale')) | \
              jinja_env(paths=[os.path.join(CURDIR, 'templates')],
                        FormEnvCls=FormEnvironment) | Map(*chains)
        return app

    def run_app(self, app, url='/'):
        rctx = RequestContext(Request.blank(url).environ)
        app(rctx) # XXX is it right?
        return rctx

    def test_language_support(self):
        app = self.get_app(languages=['en', 'ru'])
        rctx = self.run_app(app)
        self.assertEqual(rctx.conf.languages, ['en', 'ru'])
        self.assertEqual(rctx.conf.language, 'en')
        assert isinstance(rctx.vals.translation, GNUTranslations)
        #self.assertEqual(rctx.translation.plural, 'en')

    def test_set_lang(self):
        def test_backdoor(rctx):
            rctx.language = rctx.conf.language

        app = self.get_app(languages=['en', 'ru'], chains=[
                set_lang('ru') | test_backdoor,
            ])
        rctx = self.run_app(app)
        self.assertEqual(rctx.conf.languages, ['en', 'ru'])
        self.assertEqual(rctx.language, 'ru')
        assert isinstance(rctx.vals.translation, GNUTranslations)

    def test_ntranslation(self):
        app = self.get_app(languages=['ru'])
        rctx = self.run_app(app)

        # assert that plural forms are Russian
        self.assertEqual(rctx.vals.translation.plural(51), 0)
        self.assertEqual(rctx.vals.translation.plural(52), 1)
        self.assertEqual(rctx.vals.translation.plural(55), 2)

        args = (EN_SINGLE, EN_PLURAL, 2)
        t_rctx = rctx.vals.translation.ungettext(*args)
        t_form = rctx.vals.form_env.ngettext(*args)

        self.assertEqual(t_rctx, t_form)
        self.assertEqual(t_rctx, RU_PLURAL_1)

    def test_translation_forms(self):
        from insanities.forms import form, fields, widgets, convs
        from webob.multidict import MultiDict

        class SampleForm(form.Form):
            fields=[fields.Field('name', #label=M_(EN_SINGLE, EN_PLURAL, 'n'),
                                 n=22, conv=convs.Int(min=10)),
                    fields.Field('name2', #label=N_('required field'),
                                 widget=widgets.Widget(template='myinput')),
                    ]

        app = self.get_app(languages=['ru'])
        rctx = self.run_app(app)

        frm = SampleForm(rctx.vals.form_env)
        frm.accept(MultiDict({'name': 0}))
        rendered = frm.render()

        #assert RU_PLURAL_1 in rendered
        #assert u'обязательное поле' in rendered
        assert u'удалить' in rendered
        assert u'минимальное допустимое значение: 10' in rendered


    #def test_translation_templates(self):
    #    raise NotImplementedError()

    #def test_make(self):
    #    class Config(object):
    #        pass
    #    command = gettext_commands(Config())
    #    raise NotImplementedError()

    def test_compile(self):
        command = gettext_commands(modir=os.path.join(CURDIR, 'mo'),
                                   domain='test', pofiles= [
                os.path.join(CURDIR, 'locale/%s/LC_MESSAGES/test.po'),
                os.path.join(INSANITIES_ROOT, 'locale/%s/LC_MESSAGES/insanities-core.po'),
            ])
        command.command_compile(locale='ru', dbg=True)

        outfile_dbg = os.path.join(CURDIR, 'mo/ru/LC_MESSAGES/_dbg.po')
        with open(outfile_dbg) as pofile:
            string = pofile.read().decode('utf-8')
            logger.debug(string)
            assert 'Plural-Forms:' in string
            assert u"временный файл v2" in string
            assert u"специальныйтестовыймессидж" in string
            assert u"удалить" in string

        assert os.path.isfile(os.path.join(CURDIR, 'mo/ru/LC_MESSAGES/test.mo'))


if __name__ == '__main__':
    unittest.main()
