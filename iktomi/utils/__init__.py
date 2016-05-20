# -*- coding: utf-8 -*-
import six

from xml.sax import saxutils
import weakref, re, sys

from iktomi.utils.i18n import M_, N_ # deprecated, import from iktomi.utils.i18n

def quoteattr(value):
    '''Works like quoteattr from saxutils (returns escaped string in quotes),
    but is safe for HTML'''
    if value == '':
        return '""'
    return '"{}"'.format(saxutils.escape(value, {'"': '&quot;'}))

def quoteattrs(data):
    '''Takes dict of attributes and returns their HTML representation'''
    items = []
    for key, value in data.items():
        items.append('{}={}'.format(key, quoteattr(value)))
    return ' '.join(items)

def quote_js(text):
    '''Quotes text to be used as JavaScript string in HTML templates. The
    result doesn't contain surrounding quotes.'''
    if isinstance(text, six.binary_type):
        text = text.decode('utf-8') # for Jinja2 Markup
    text = text.replace('\\', '\\\\');
    text = text.replace('\n', '\\n');
    text = text.replace('\r', '');
    for char in '\'"<>&':
        text = text.replace(char, '\\x{:02x}'.format(ord(char)))
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


class cached_class_property(object):
    '''Turns decorated method into caching class property (method is called
    once on first access to property of class or any of its instances).'''

    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__

    def __get__(self, inst, cls):
        result = self.method(cls)
        setattr(cls, self.name, result)
        return result


# http://www.w3.org/TR/REC-xml/#NT-Char
# Char ::= #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | 
#          [#x10000- #x10FFFF]
# (any Unicode character, excluding the surrogate blocks, FFFE, and FFFF)
_char_tail = ''
if sys.maxunicode > 0x10000:
    _char_tail = u'{}-{}'.format(six.unichr(0x10000),
                                 six.unichr(min(sys.maxunicode, 0x10FFFF)))
_nontext_sub = re.compile(
            u'[^\\x09\\x0A\\x0D\\x20-\uD7FF\uE000-\uFFFD{}]'.format(_char_tail),
            re.U).sub
def replace_nontext(text, replacement=u'\uFFFD'):
    return _nontext_sub(replacement, text)


