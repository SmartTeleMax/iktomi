# -*- coding: utf-8 -*-

from . import M_

class FormEnvironmentMixin(object):
    '''
    Mixin adding get_string method to environment
    '''

    def get_string(self, msg, args={}):
        if isinstance(msg, M_) and msg.multiple_by:
            return self.rctx.translation.ungettext(msg, args[msg.multiple_by])
        return self.rctx.translation.ugettext(msg)
