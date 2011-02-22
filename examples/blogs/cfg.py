# -*- coding: utf-8 -*-

import sys
from os import path

cur_dir = path.abspath('.')

def rel(*args):
    args = [cur_dir] + list(args)
    return path.join(*args)


TEMPLATES = rel('templates')

STATIC = rel('static')

DATABASES = {"": 'sqlite+pysqlite:///'+rel('data.db')}

MEMCACHED = ['localhost:11211']

# =========== I18N =======
LOCALEDIR = rel('locale')
MODIR = rel('mo')

import insanities
insanities_dir = path.dirname(insanities.__file__)
POFILES = [
    # first language is prior
    path.join(LOCALEDIR, '%s/LC_MESSAGES/insanities.po'),
    path.join(insanities_dir, 'locale/%s/LC_MESSAGES/insanities-core.po')
]
LANGUAGES = ['en', 'ru']
