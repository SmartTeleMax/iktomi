# -*- coding: utf-8 -*-
import json
from webob.exc import status_map, HTTPMethodNotAllowed
from webob import Response
from .core import cases
from . import filters

__all__ = ['redirect_to', 'to_json', 'Rule']

def redirect_to(endpoint, _code=303, qs=None, **kwargs):
    def handle(env, data):
        url = env.root.build_url(endpoint, **kwargs)
        if qs is not None:
            url = url.qs_set(qs)
        raise status_map[_code](location=str(url))
    return handle


def to_json(data):
    return Response(json.dumps(data))


def Rule(path, handler, method=None, name=None, convs=None):
    # werkzeug-style Rule
    if name is None:
        name = handler.func_name
    h = filters.match(path, name, convs=convs)
    if method is not None:
        h = h | cases(filters.method(method),
                      HTTPMethodNotAllowed)
    return h | handler

