# -*- coding: utf-8 -*-

from xml.sax import saxutils
import weakref, re, sys


def quoteattr(value):
    """
    works like quoteattr from saxutils
    """
    if value == '':
        return '""'
    return '%s' % saxutils.escape(unicode(value), {'"': '&quot;'})

def quoteattrs(data):
    """
    takes dict of attrs and return correct
    xhtml representation
    """
    items = []
    for key, value in data.items():
        items.append('%s="%s"' % (key, quoteattr(value)))
    return ' '.join(items)

def quote_js(text):
    '''Quotes text to be used as JavaScript string in HTML templates. The
    result doesn't contain surrounding quotes.'''
    text = text.replace('\\', '\\\\');
    text = text.replace('\n', '\\n');
    text = text.replace('\r', '');
    for char in '\'"<>&':
        text = text.replace(char, '\\x%2x' % ord(char))
    return text

def weakproxy(obj):
    '''Safe version of weakref.proxy.'''
    try:
        obj = weakref.proxy(obj)
    except TypeError:
        pass
    return obj


class cached_property(object):
    '''Turns decorated method into caching property (method is called once on
    first access to property).'''

    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__
        self.__doc__ = method.__doc__

    def __get__(self, inst, cls):
        if inst is None:
            return self
        result = self.method(inst)
        setattr(inst, self.name, result)
        return result


# http://www.w3.org/TR/REC-xml/#NT-Char
# Char ::= #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | 
#          [#x10000- #x10FFFF]
# (any Unicode character, excluding the surrogate blocks, FFFE, and FFFF)
_char_tail = ''
if sys.maxunicode > 0x10000:
    _char_tail = u'%s-%s' % (unichr(0x10000),
                             unichr(min(sys.maxunicode, 0x10FFFF)))
_nontext_sub = re.compile(
                ur'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD%s]' % _char_tail,
                re.U).sub
def replace_nontext(text, replacement=u'\uFFFD'):
    return _nontext_sub(replacement, text)

def conf_to_dict(cfg):
    '''Selects all module members which names are upper case and return dict'''
    keys = filter(lambda x: x.isupper(), dir(cfg))
    d = {}
    for key in keys:
        d[key] = getattr(cfg, key)
    return d


# i18n markers
def N_(msg):
    '''Single translatable string marker'''
    return msg

class M_(unicode):
    '''Marker for translatable string with plural form'''
    def __new__(cls, single, plural):
        self = unicode.__new__(cls, single)
        self.plural = plural
        return self

def smart_gettext(translation, msg, count=None):
    '''If msg is instance of M_ returns multiple translation
    otherwise return single translation'''
    if count is None:
        count = 1
    if isinstance(msg, M_) and count is not None:
        return translation.ungettext(msg, msg.plural, count)
    return translation.ugettext(msg)


