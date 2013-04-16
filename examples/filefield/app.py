# -*- coding: utf-8 -*-
from iktomi import web
from iktomi.web.filters import *
from iktomi.templates import jinja2, Template
from environment import Environment

import cfg
import handlers as h

static = static_files(cfg.STATIC)
media = static_files(cfg.MEDIA, '/media/')
template = Template(cfg.TEMPLATES, jinja2.TEMPLATE_DIR, engines={'html': jinja2.TemplateEngine})


app = web.cases(
    static, media,
    match('/', 'files') | web.cases(
        # Playing REST ;)
        method('GET') | h.list_files,
        method('POST') | h.post_file,
        #method('DELETE') | h.delete_files,
    ),
)

wsgi_app = web.Application(app, env_class=Environment)

