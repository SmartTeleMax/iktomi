# -*- coding: utf-8 -*-

from xml.sax import saxutils
import weakref, re, sys


def quoteattr(value):
    '''Works like quoteattr from saxutils (returns escaped string in quotes),
    but is safe for HTML'''
    if value == '':
        return '""'
    return '"{}"'.format(saxutils.escape(unicode(value), {'"': '&quot;'}))

def quoteattrs(data):
    '''Takes dict of attributes and returns their HTML representation'''
    items = []
    for key, value in data.items():
        items.append('{}={}'.format(key, quoteattr(value)))
    return ' '.join(items)

def quote_js(text):
    '''Quotes text to be used as JavaScript string in HTML templates. The
    result doesn't contain surrounding quotes.'''
    text = unicode(text) # for Jinja2 Markup
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
    _char_tail = u'{}-{}'.format(unichr(0x10000),
                                 unichr(min(sys.maxunicode, 0x10FFFF)))
_nontext_sub = re.compile(
            ur'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD{}]'.format(_char_tail),
            re.U).sub
def replace_nontext(text, replacement=u'\uFFFD'):
    return _nontext_sub(replacement, text)


# i18n markers
def N_(msg):
    '''
    Single translatable string marker.
    Does nothing, just a marker for \\*.pot file compilers.

    Usage::

        n = N_('translate me')
        translated = env.gettext(n)
    '''
    return msg


class M_(object):
    '''
    Marker for translatable string with plural form.
    Does not make a translation, just incapsulates a data about
    the translatable string.

    :param single: a single form
    :param plural: a plural form. Count can be included in %\-format syntax
    :param count_field: a key used to format

    Usage::

        message = M_(u'max length is %(max)d symbol',
                     u'max length is %(max)d symbols',
                     count_field="max")
        m = message % {'max': 10}
        trans = env.ngettext(unicode(m.single),
                             unicode(m.plural),
                             m.count
                             ) % m.format_args
    '''
    def __init__(self, single, plural, count_field='count', format_args=None):
        self.single = single
        self.plural = plural
        self.count_field = count_field
        self.format_args = format_args

    def __mod__(self, format_args):
        '''
        Returns a copy of the object with bound formatting args (as dict).
        A key equal to `count_field` must be in `format_args`.
        '''
        return self.__class__(self.single, self.plural, count_field=self.count_field,
                              format_args=format_args)

    @property
    def count(self):
        '''
        A count based on `count_field` and `format_args`.
        '''
        args = self.format_args
        if args is None or \
                (isinstance(args, dict) and self.count_field not in args):
            raise TypeError("count is required")
        return args[self.count_field] if isinstance(args, dict) else args

    def __unicode__(self):
        args = self.format_args
        if self.count == 1:
            return self.single % args
        return self.plural % args





