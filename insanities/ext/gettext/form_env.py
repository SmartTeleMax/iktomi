# -*- coding: utf-8 -*-

from . import M_

class FormEnvironmentMixin(object):
    '''
    Mixin adding get_string method to environment
    '''

    def get_string(self, msg, args={}):
        tr = self.rctx.translation
        if isinstance(msg, M_) and msg.multiple_by:
            return tr.ungettext(msg, msg.plural, args[msg.multiple_by])
        return tr.ugettext(msg)
