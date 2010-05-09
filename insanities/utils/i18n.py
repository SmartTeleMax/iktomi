# -*- coding: utf-8 -*-
import gettext


def N_(msg):
    '''gettext marker'''
    return msg

class M_(unicode):
    def __new__(cls, single, plural, multiple_by=None):
        self = unicode.__new__(cls, single)
        self.plural = plural
        self.multiple_by = multiple_by
        return self


def smart_gettext(translation, msg, args={}):
    if isinstance(msg, M_) and msg.multiple_by:
        return translation.ungettext(msg, msg.plural,
                                     args[msg.multiple_by])
    return translation.ugettext(msg)


