# -*- coding: utf-8 -*-

__all__ = ['ask']

from .http import Request
from .reverse import Reverse
from .app import AppEnvironment, Application
from ..utils.storage import VersionedStorage


def ask(handler, url, method=None, data=None,
        headers=None, additional_env=None, additional_data=None,
        EnvCls=None):
    if isinstance(handler, Application):
        EnvCls = EnvCls or handler.EnvCls
        handler = handler.handler

    EnvCls = EnvCls or AppEnvironment
    root = Reverse.from_handler(handler)
    rq_kw = dict(method=method.upper()) if method else {}
    request = Request.blank(url, POST=data, headers=headers, **rq_kw)
    env = VersionedStorage(EnvCls, request, root, **(additional_env or {}))
    #TODO: may be later process cookies separatly
    data = VersionedStorage(**(additional_data or {}))
    return handler(env, data)
