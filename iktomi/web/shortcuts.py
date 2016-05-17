# -*- coding: utf-8 -*-
from webob.exc import status_map, HTTPMethodNotAllowed
from .core import cases
from . import filters

__all__ = ['redirect_to', 'Rule']

def redirect_to(endpoint, _code=303, qs=None, **kwargs):
    def handle(env, data):
        url = env.root.build_url(endpoint, **kwargs)
        if qs is not None:
            url = url.qs_set(qs)
        raise status_map[_code](location=str(url.with_host()))
    return handle


def Rule(path, handler, method=None, name=None, convs=None):
    # werkzeug-style Rule
    if name is None:
        name = handler.__name__
    h = filters.match(path, name, convs=convs)
    if method is not None:
        h = h | cases(filters.method(method),
                      HTTPMethodNotAllowed)
    return h | handler

