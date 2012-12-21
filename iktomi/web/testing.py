# -*- coding: utf-8 -*-

__all__ = ['ask']

from .http import Request
from .reverse import Reverse
from ..utils.storage import VersionedStorage


def ask(application, url, method='get', data=None,
        headers=None, additional_env=None, additional_data=None,
        EnvCls=None):
    EnvCls = EnvCls or application.EnvCls
    root = Reverse.from_handler(application)
    request = Request.blank(url, POST=data, headers=headers)
    env = VersionedStorage(EnvCls, request, root, **(additional_env or {}))
    #TODO: may be later process cookies separatly
    data = VersionedStorage(**(additional_data or {}))
    return application(env, data)
