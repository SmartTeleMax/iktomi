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


class LanguageSupport(RequestHandler):
    """
    Request handler addding support of i18n

    :*languages* - languages ("en", "ru") or locales ("en_GB", "ru_RU") code.
    The first language is default.

    :*localepath* - a path to locale directory containing .mo file.

    :*domain* - gettext domain of translation
    """

    def __init__(self, languages, localepath, domain='insanities'):
        super(LanguageSupport, self).__init__()
        self.languages = languages
        self.default_language = languages[0]
        self.localepath = localepath
        self.domain = domain
        self.translation_set = {}
        
    def handle(self, rctx):
        rctx._language_handler = self
        self.activate(rctx, self.default_language)
        raise ContinueRoute(self)
        
    def get_translation(self, language):
        """
        Returns a translation object.

        Adds a fallback to language without locale, if a language is particular
        locale and has not translation.

        Adds a fallback to the default language, if it's
        different from the requested language.
        
        :*language* - language ("en", "ru") or locale ("en_GB", "ru_RU") code.
        """
        # XXX normalize locale

        res = self.translation_set.get(language)
        if res is not None:
            return res

        if os.path.isdir(self.localepath):
            try:
                res = gettext.translation(self.domain, self.localepath, [language])
            except IOError, e:
                if '_' in language:
                    res = self.get_translation(language.split('_')[0])
                elif language != self.default_language:
                    res = self.get_translation(self.default_language)
                else:
                    return gettext.NullTranslations()

        self.translation_set[language] = res
        return res

    def activate(self, rctx, language):
        rctx.translation = self.get_translation(self.language)
        rctx.language = language
        rctx.data['gettext'] = rctx.translation.ugettext
        rctx.data['ngettext'] = rctx.translation.ungettext


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
        rctx._language_handler.activate(rctx, self.language)
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
