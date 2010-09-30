# -*- coding: utf-8 -*-
from insanities.web import *
from insanities.web.filters import *
from insanities.web.wrappers import *

from insanities.ext.jinja2 import render_to, jinja_env
from insanities.ext.cache import local_cache_env
from insanities.utils import conf_to_dict


import cfg
import handlers as h

static = static_files(cfg.STATIC)
media = static_files(cfg.MEDIA, '/media/')

env = Conf(**conf_to_dict(cfg)) | jinja_env(extensions=['jinja2.ext.i18n']) | local_cache_env()

# should be added only in local app, but for simplicity added immediatelly
env = env | static.add_reverse

app = env | Map(
    static, media,
    match('/', 'files') | Map(
        # Playing REST ;)
        method('GET') | h.list_files | render_to('index.html'),
        method('POST') | h.post_file | render_to('index.html'),
        #method('DELETE') | h.delete_files,
    ),
)
