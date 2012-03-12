# -*- coding: utf-8 -*-
import json
from webob.exc import status_map
from webob import Response

from .filters import match

def redirect_to(endpoint, _code=303, qs=None, **kwargs):
    def handle(env, data, nxt):
        # to make this work, we should fix env.reverse name
        url = env.reverse.url_for(endpoint, **kwargs)
        if qs is not None:
            url = url.qs_set(qs)
        raise status_map[_code](location=str(url))
    return handle

def http_error(_code, **kwargs):
    def handle(env, data, nxt):
        raise status_map[_code](**kwargs)
    return handle

def to_json(data):
    return Response(json.dumps(data))

def Rule(path, handler, method=None):
    # werkzeug-style Rule
    h = match(path, handler.func_name)
    if method is not None:
        h = h | method(method)
    return h | handler

