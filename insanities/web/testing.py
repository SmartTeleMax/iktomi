# -*- coding: utf-8 -*-

__all__ = ['ask']

from .http import Request
from ..utils.storage import VersionedStorage


def ask(application, url, method='get', data=None, headers=None):
    env = VersionedStorage()
    #TODO: may be later process cookies separatly
    env.request = Request.blank(url, POST=data, headers=headers)
    data = VersionedStorage()
    return application(env, data)
