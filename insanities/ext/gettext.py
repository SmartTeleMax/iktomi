# -*- coding: utf-8 -*-
# XXX
from __future__ import absolute_import

import os
import re
import sys
import locale
import gettext
import pprint
from itertools import dropwhile
from subprocess import PIPE, Popen

from insanities.management.commands import CommandDigest
from insanities.web import RequestHandler


import logging
logger = logging.getLogger(__name__)


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
        # XXX or lookup languages, localepath and domain in rctx.conf?
        self.languages = languages
        self.default_language = languages[0]
        self.localepath = localepath
        self.domain = domain
        self.translation_set = {}

    def handle(self, rctx):
        rctx.vals['language_handler'] = self
        rctx.conf['languages'] = self.languages
        self.activate(rctx, self.default_language)
        return rctx

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
        rctx.vals['translation'] = self.get_translation(language)
        rctx.conf['language'] = language
        # XXX what's better: rctx.vals.N_ or rctx.vals.gettext?
        # Or maybe it's more useful to make shortcuts from rctx like: rctx.N_?
        rctx.vals['gettext'] = rctx.data['N_'] = rctx.vals.translation.ugettext
        rctx.vals['ngettext'] = rctx.data['M_'] = rctx.vals.translation.ungettext


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
        rctx.vals.language_handler.activate(rctx, self.language)
        return rctx


class gettext_commands(CommandDigest):
    ''''''

    plural_forms_re = re.compile(r'^(?P<value>"Plural-Forms.+?\\n")\s*$',
                                 re.MULTILINE | re.DOTALL)

    def __init__(self, localedir=None, searchdir=None, modir=None, domain='insanities',
                 extensions=('html',),   ignore=[], pofiles=None):
        """
        --localedir     Directory containig locale files
        --searchdir     Directory containig source code files
        --domain        The domain of the message files (default: "insanities").
        --extensions    The file extension(s) to examine (default: ".html", separate multiple extensions with commas).
        --ignore        Ignore files or directories matching this glob-style pattern. Use multiple times to ignore more.
        """
        self.extensions = [x.lstrip('.') for x in extensions]
        self.domain = domain
        self.localedir = localedir
        self.modir = modir or localedir
        self.searchdir = searchdir
        self.ignore = ignore
        self.pofiles = pofiles

    def command_make(self, locale=None, domain=None, verbosity='1'):
        """
        --locale        Creates or updates the message files only for the given locale (e.g. pt_BR).
        --verbosity     Verbosity.
        """
        domain = domain or self.domain

        ignore_patterns = ['*/.*', '*~'] + self.ignore

        if locale is None:
            sys.stdout.write(self.__class__.command_make.__doc__)
            raise Exception() # what exception we need to raise?

        self.check_gettext()

        basedir = os.path.join(self.localedir, locale, 'LC_MESSAGES')
        if not os.path.isdir(basedir):
            os.makedirs(basedir)

        pofile = os.path.join(basedir, '%s.po' % domain)
        potfile = os.path.join(basedir, '%s.pot' % domain)

        if os.path.exists(potfile):
            os.unlink(potfile)

        for dirpath, file in self.find_files(self.searchdir, ignore_patterns, verbosity):
            file_base, file_ext = os.path.splitext(file)

            if file_ext == '.py' or file_ext[1:] in self.extensions:
                if verbosity > 1:
                    sys.stdout.write('processing file %s in %s\n' % (file, dirpath))

                cmd = 'xgettext -d %s -L Python --keyword=N_ --keyword=M_:1,2 --from-code UTF-8 -o - "%s"' % (
                    domain, os.path.join(dirpath, file))
                msgs, errors = self._popen(cmd)
                if errors:
                    raise Exception("errors happened while running xgettext on %s\n%s" % (file, errors))

                if os.path.exists(potfile):
                    # Strip the header
                    msgs = '\n'.join(dropwhile(len, msgs.split('\n')))
                else:
                    msgs = msgs.replace('charset=CHARSET', 'charset=UTF-8')
                if msgs:
                    open(potfile, 'ab').write(msgs)

        if os.path.exists(potfile):
            msgs, errors = self._popen('msguniq --to-code=utf-8 "%s"' % potfile)
            if errors:
                raise Exception("errors happened while running msguniq\n%s" % errors)
            open(potfile, 'w').write(msgs)
            if os.path.exists(pofile):
                msgs, errors = self._popen('msgmerge -q "%s" "%s"' % (pofile, potfile))
                if errors:
                    raise Exception("errors happened while running msgmerge\n%s" % errors)
            open(pofile, 'wb').write(msgs)
            os.unlink(potfile)

    def command_compile(self, locale=None, domain=None, dbg=False):
        """
        --locale        Compiles the message files only for the given locale.
        --domain        Domain to output. Default is 'insanities'
        --dbg           Set if you want to debug .po file wil be outputted
                        to LC_MESSAGES/_dbg.po.
        """
        import polib
        domain = domain or self.domain

        assert self.pofiles

        if locale is None:
            sys.stdout.write(self.__class__.command_compile.__doc__)
            raise Exception() # what exception we need to raise?

        result = plural = None
        if '_' in locale:
            # for example: en translations are merged into en_GB
            locales = (locale, locale.split('_')[0])
        else:
            locales = [locale]

        for lcl in locales:
            for fpath in self.pofiles[1:]:

                file = fpath % lcl
                if not os.path.isfile(file):
                    sys.stdout.write('skipping file %s\n' % file)
                    continue
                if result is None:
                    # first found file
                    result = polib.pofile(self.pofiles[0] % locale)
                    plural = result.metadata.get('Plural-Forms')
                    logger.debug('First found file: %s' % file)
                    logger.debug('Plural forms is: %s' % plural)
                    logger.debug('Metadata: %s' % pprint.pformat(result.metadata))
                    continue

                logger.debug('Merging file: %s' % file)
                pofile = polib.pofile(file)

                for entry in pofile:
                    old_entry = result.find(entry.msgid, by='msgid')

                    if old_entry is None:
                        result.append(entry)
                    elif not old_entry.msgstr and entry.msgstr:
                        # XXX check if it is correct
                        old_entry.msgstr = entry.msgstr

                new_plural = pofile.metadata.get('Plural-Forms')
                if not plural and new_plural:
                    logger.debug('Plural forms is: %s' % plural)
                    result.metadata['Plural-Forms'] = new_plural

        out_path = os.path.join(self.modir, locale, 'LC_MESSAGES/%s.mo' % domain)
        if not os.path.isdir(os.path.dirname(out_path)):
            os.makedirs(os.path.dirname(out_path))
        result.save_as_mofile(out_path) #are plural expressions saved correctly?

        if dbg:
            out_path = os.path.join(self.modir, locale, 'LC_MESSAGES/_dbg.po')
            result.save(out_path)

    # ============ Helper methods ===============
    # XXX staff from Django. need to be refactored
    def _popen(self, cmd):
        """
        Friendly wrapper around Popen for Windows
        """
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE,
                  close_fds=os.name != 'nt', universal_newlines=True)
        return p.communicate()

    def is_ignored(self, path, ignore_patterns):
        """
        Helper function to check if the given path should be ignored or not.
        """
        import fnmatch
        for pattern in ignore_patterns:
            if pattern and fnmatch.fnmatchcase(path, pattern):
                return True
        return False

    def check_gettext(self):
        # We require gettext version 0.15 or newer.
        output = self._popen('xgettext --version')[0]
        match = re.search(r'(?P<major>\d+)\.(?P<minor>\d+)', output)
        if match:
            xversion = (int(match.group('major')), int(match.group('minor')))
            if xversion < (0, 15):
                raise Exception('Internationalization requires GNU gettext'
                ' 0.15 or newer. You are using version %s, please upgrade '
                'your gettext toolset.' % match.group())

    def find_files(self, root, ignore_patterns, verbosity):
        """
        Helper function to get all files in the given root.
        """
        all_files = []
        for (dirpath, dirnames, filenames) in os.walk(root):
            for f in filenames:
                norm_filepath = os.path.normpath(os.path.join(dirpath, f))
                if self.is_ignored(norm_filepath, ignore_patterns):
                    if verbosity > 1:
                        sys.stdout.write('ignoring file %s in %s\n' % (f, dirpath))
                else:
                    all_files.extend([(dirpath, f)])
        all_files.sort()
        return all_files

 
