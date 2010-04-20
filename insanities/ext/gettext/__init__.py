# -*- coding: utf-8 -*-

import locale
import gettext
import os

from insanities.web.core import RequestHandler
from .commands import gettext_commands
# global translations cache
_translations = {}



def N_(msg):
    '''gettext marker'''
    return msg

def translation(localepath, language, default_language):
    """
    Returns a translation object.

    It will construct a object for the requested language and add a fallback
    to the default language, if it's different from the requested language.
    """
    global _translations
    
    t = _translations.get(language, None)
    if t is not None:
        return t

    loc = to_locale(lang)

    res = _translations.get(lang, None)
    if res is not None:
        return res

    # xxx
    if os.path.isdir(localepath):
        try:
            t = gettext.translation('insanities-compiled', localepath, [loc])
            t.set_language(lang)
        except IOError, e:
            t = None

    if res is None and language != default_language:
        res = translation(default_language)
    elif res is None:
        return gettext_module.NullTranslations()

    _translations[lang] = res

    return res


class LanguageSupport(RequestHandler):

    def __init__(self, languages, localepath):
        super(static, self).__init__()
        self.languages = languages
        self.default_language = languages[0]
        self.localepath = localepath
        
    def handle(self, rctx):
        rctx.languages = self.languages
        rctx.language = rctx.default_language = self.default_language
        rctx.translation = translation(self.localepath,
                                       self.default_language,
                                       self.default_language)
        raise ContinueRoute(self)


class set_lang(RequestHandler):
    '''
    usage::
    
        Map(
            subdomain('ru') | set_lang('ru_RU') | ...,
            subdomain('en') | set_lang('en_US') | ...
        )
    '''

    def __init__(self, language):
        super(static, self).__init__()
        self.language = language

    def handle(self, rctx):
        rctx.translation = translation(self.language,
                                       rctx.default_language)


