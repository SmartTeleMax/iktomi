# -*- coding: utf-8 -*-
import locale
import gettext
import os

from insanities.web import RequestHandler, ContinueRoute

from .commands import gettext_commands


def N_(msg):
    '''gettext marker'''
    return msg

class M_(unicode):
    def __new__(cls, single, plural, multiple_by=None):
        self = unicode.__new__(cls, single)
        self.plural = plural
        self.multiple_by = multiple_by
        return self

# global translations cache
_translations = {}

def translation(localepath, language, default_language, domain):
    """
    Returns a translation object.

    It will construct a object for the requested language and add a fallback
    to the default language, if it's different from the requested language.
    """
    global _translations
    
    # XXX normalize locale

    res = _translations.get(language, None)
    if res is not None:
        return res

    if os.path.isdir(localepath):
        try:
            res = gettext.translation(domain, localepath, [language])
        except IOError, e:
            pass

    if res is None and language != default_language:
        res = translation(localepath, default_language, default_language, domain)
    elif res is None:
        return gettext.NullTranslations()

    _translations[language] = res

    return res


def _apply_translation_to_rctx(rctx, language, translation):
    rctx.language = language
    rctx.data['gettext'] = translation.ugettext
    rctx.data['ngettext'] = translation.ungettext


class LanguageSupport(RequestHandler):

    def __init__(self, languages, localepath, domain='insanities'):
        super(LanguageSupport, self).__init__()
        self.languages = languages
        self.default_language = languages[0]
        self.localepath = localepath
        self.domain = domain
        
    def handle(self, rctx):
        rctx.languages = self.languages
        rctx.default_language = self.default_language
        rctx.localepath = self.localepath
        rctx.localedomain = self.domain
        rctx.translation = translation(self.localepath,
                                       self.default_language,
                                       self.default_language,
                                       self.domain)
        _apply_translation_to_rctx(rctx, self.default_language, rctx.translation)
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
        super(set_lang, self).__init__()
        self.language = language

    def handle(self, rctx):
        rctx.translation = translation(rctx.localepath,
                                       self.language,
                                       rctx.default_language,
                                       rctx.localedomain)
        _apply_translation_to_rctx(rctx, self.language, rctx.translation)
        return rctx

class FormEnvironmentMixin(object):
    '''
    Mixin adding get_string method to environment
    '''

    def gettext(self, msg, args={}):
        if isinstance(msg, M_) and msg.multiple_by:
            return self.ngettext(msg, msg.plural, args[msg.multiple_by])
        return self.rctx.translation.ugettext(msg)

    def ngettext(self, single, plural, count):
        return self.rctx.translation.ungettext(single, plural, count)
