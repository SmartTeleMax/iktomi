# -*- coding: utf-8 -*-

__all__ = ['ask']

from .http import Request
from ..utils.stacked_dict import StackedDict


def ask(application, url, method='get', data=None, headers=None):
    env = StackedDict()
    #TODO: may be later process cookies separatly
    env.request = Request.blank(url, POST=data, headers=headers)
    data = StackedDict()
    return application(env, data)
