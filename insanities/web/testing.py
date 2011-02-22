# -*- coding: utf-8 -*-

__all__ = ['ask']

from .http import Request
from ..utils.storage import VersionedStorage


def ask(application, url, method='get', data=None,
        headers=None, additional_env=None, additional_data=None):
    env = VersionedStorage(additional_env or {})
    #TODO: may be later process cookies separatly
    env.request = Request.blank(url, POST=data, headers=headers)
    data = VersionedStorage(additional_data or {})
    return application(env, data)
