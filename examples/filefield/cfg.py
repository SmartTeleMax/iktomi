# -*- coding: utf-8 -*-

from os import path
from iktomi.templates import jinja2 as jnj2

cur_dir = path.abspath(path.dirname(__file__))
RUN_DIR = path.join(cur_dir, 'run')
LOG_DIR = path.join(cur_dir, 'log')
IKTOMI_FORMS_DIR = path.dirname(path.abspath(jnj2.__file__))

def rel(*args):
    args = [cur_dir] + list(args)
    return path.join(*args)


TEMPLATES = [rel('templates'),
             path.join(IKTOMI_FORMS_DIR, 'templates')]

STATIC = rel('static')
MEDIA = rel('media')

# Do not change defaults, overwrite params in FASTCGI_PARAMS instead
FASTCGI_PREFORKED_DEFAULTS = dict(
    preforked=True,
    multiplexed=False,
    minSpare=1,
    maxSpare=5,
    maxChildren=50,
    maxRequests=0,
)

FASTCGI_PARAMS = dict(
    FASTCGI_PREFORKED_DEFAULTS,
    maxSpare=8,
    minSpare=8,
    maxChildren=2,
)

FLUP_ARGS = dict(
    fastcgi_params = FASTCGI_PARAMS,
    umask = 0,
    bind = path.join(RUN_DIR, 'admin.sock'),
    pidfile = path.join(RUN_DIR, 'admin.pid'),
    logfile = path.join(LOG_DIR, 'admin.log'),
)
