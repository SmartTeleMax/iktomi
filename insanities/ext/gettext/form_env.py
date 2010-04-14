# -*- coding: utf-8 -*-

from . import M_

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
