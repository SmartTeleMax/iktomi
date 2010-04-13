# -*- coding: utf-8 -*-

import os
import re
import sys
from itertools import dropwhile

from insanities.management.commands import CommandDigest
from subprocess import PIPE, Popen


class gettext_commands(CommandDigest):
    ''''''

    def check_gettext(self):
        # We require gettext version 0.15 or newer.
        output = _popen('xgettext --version')[0]
        match = re.search(r'(?P<major>\d+)\.(?P<minor>\d+)', output)
        if match:
            xversion = (int(match.group('major')), int(match.group('minor')))
            if xversion < (0, 15):
                raise Exception("Internationalization requires GNU gettext 0.15 or newer. You are using version %s, please upgrade your gettext toolset." % match.group())
    
    def find_files(self, root, ignore_patterns, verbosity):
        """
        Helper function to get all files in the given root.
        """
        all_files = []
        for (dirpath, dirnames, filenames) in os.walk(root):
            for f in filenames:
                norm_filepath = os.path.normpath(os.path.join(dirpath, f))
                if is_ignored(norm_filepath, ignore_patterns):
                    if verbosity > 1:
                        sys.stdout.write('ignoring file %s in %s\n' % (f, dirpath))
                else:
                    all_files.extend([(dirpath, f)])
        all_files.sort()
        return all_files
    
    def command_make(self, locale=None, localedir=None, domain='insanities', verbosity='1',
            extensions='html', ignore='', searchdir='.'):
        """
        --locale        Creates or updates the message files only for the given locale (e.g. pt_BR).
        --domain        The domain of the message files (default: "insanities").
        --extensions    The file extension(s) to examine (default: ".html", separate multiple extensions with commas).
        --ignore        Ignore files or directories matching this glob-style pattern. Use multiple times to ignore more.
        --verbosity     Verbosity.
        """
        extensions = [x.lstrip('.') for x in extensions.split(',')]
        ignore_patterns = ignore.split(';') + ['.*', '*~']
        
        if localedir is None:
            localedir = os.path.abspath('locale')
     
        if locale is None or domain is None:
            sys.stdout.write(self.__class__.command_make.__doc__)
            raise Exception() # what exception we need to raise?
    
        self.check_gettext()
        
        basedir = os.path.join(localedir, locale, 'LC_MESSAGES')
        if not os.path.isdir(basedir):
            os.makedirs(basedir)

        pofile = os.path.join(basedir, '%s.po' % domain)
        potfile = os.path.join(basedir, '%s.pot' % domain)

        if os.path.exists(potfile):
            os.unlink(potfile)
            
        for dirpath, file in self.find_files(searchdir, ignore_patterns, verbosity):
            file_base, file_ext = os.path.splitext(file)
            
            if file_ext == '.py' or file_ext[1:] in extensions:
                if verbosity > 1:
                    sys.stdout.write('processing file %s in %s\n' % (file, dirpath))
                
                cmd = 'xgettext -d %s -L Python --keyword=N_ --keyword=M_:1,2 --from-code UTF-8 -o - "%s"' % (
                    domain, os.path.join(dirpath, file))
                msgs, errors = _popen(cmd)
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
            msgs, errors = _popen('msguniq --to-code=utf-8 "%s"' % potfile)
            if errors:
                raise Exception("errors happened while running msguniq\n%s" % errors)
            open(potfile, 'w').write(msgs)
            if os.path.exists(pofile):
                msgs, errors = _popen('msgmerge -q "%s" "%s"' % (pofile, potfile))
                if errors:
                    raise Exception("errors happened while running msgmerge\n%s" % errors)
            open(pofile, 'wb').write(msgs)
            os.unlink(potfile)

    def command_compile(self, locale=None, localedir=None, dbg=False):
        import polib
        cfg = self.cfg
        
        if localedir is None:
            localedir = os.path.abspath('locale')
        
        result = polib.pofile(cfg.LOCALE_FILES[1] % locale)
        
        if '_' in locale:
            locales = (locale, locale.split('_')[0])
        else:
            locales = [locale]

        for fpath in cfg.LOCALE_FILES[1:]:
            for lcl in locales:
                file = fpath % lcl
                if not os.path.isfile(file):
                    sys.stdout.write('skipping file %s\n' % file)
                    continue
                
                for entry in polib.pofile(file):
                    old_entry = self.find(entry.msgid, by='msgid')
                    
                    if old_entry is None:
                        result.append(entry)
                    elif not old_entry.msgstr and entry.msgstr:
                        # XXX check if it is correct
                        old_entry.msgstr = entry.msgstr

        out_path = os.path.join(localedir, locale, 'LC_MESSAGES/insanitites.mo')
        result.save_as_mofile(out_path)
        if dbg:
            out_path = os.path.join(localedir, locale, 'LC_MESSAGES/_dbg.po')
            result.save(out_path)
        # save to mo file

# XXX staff from Django. need to be refactored
def _popen(cmd):
    """
    Friendly wrapper around Popen for Windows
    """
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, close_fds=os.name != 'nt', universal_newlines=True)
    return p.communicate()

def is_ignored(path, ignore_patterns):
    """
    Helper function to check if the given path should be ignored or not.
    """
    import fnmatch
    for pattern in ignore_patterns:
        if fnmatch.fnmatchcase(path, pattern):
            return True
    return False
