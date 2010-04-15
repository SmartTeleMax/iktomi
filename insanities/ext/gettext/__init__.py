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
    
    t = _translations.get(language, None)
    if t is not None:
        return t

    # XXX normalize locale

    res = _translations.get(language, None)
    if res is not None:
        return res

    if os.path.isdir(localepath):
        try:
            t = gettext.translation(domain, localepath, [language])
            t.set_language(lang)
        except IOError, e:
            t = None

    if res is None and language != default_language:
        res = translation(default_language)
    elif res is None:
        return gettext.NullTranslations()

    _translations[lang] = res

    return res


class LanguageSupport(RequestHandler):

    def __init__(self, languages, localepath, domain='insanities-compiled'):
        super(LanguageSupport, self).__init__()
        self.languages = languages
        self.default_language = languages[0]
        self.localepath = localepath
        self.domain = domain
        
    def handle(self, rctx):
        rctx.languages = self.languages
        rctx.language = rctx.default_language = self.default_language
        rctx.localepath = self.localepath
        rctx.translation = translation(self.localepath,
                                       self.default_language,
                                       self.default_language,
                                       self.domain)
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
        rctx.translation = translation(rctx.localepath,
                                       self.language,
                                       rctx.default_language)


class FormEnvironmentMixin(object):
    '''
    Mixin adding get_string method to environment
    '''

    def gettext(self, msg, args={}):
        if isinstance(msg, M_) and msg.multiple_by:
            return self.nget_string(msg, msg.plural, args[msg.multiple_by])
        return self.rctx.translation.ugettext(msg)

    def ngettext(self, single, plural, count):
        return self.rctx.translation.ungettext(single, plural, count)
