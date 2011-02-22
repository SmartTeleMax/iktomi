# -*- coding: utf-8 -*-
from insanities import web
from insanities.web.filters import *

import mage
from memcache import Client
from insanities.ext.auth import CookieAuth
from insanities.templates import jinja2, Template

import cfg
import models
import handlers as h

static = web.static_files(cfg.rel('static'))
db_maker = mage.sqla.construct_maker(cfg.DATABASES)
memcache_client = Client(cfg.MEMCACHED)
auth = CookieAuth(models.User.by_credential, models.User.by_id, memcache_client)
template = Template(cfg.TEMPLATES, jinja2.TEMPLATE_DIR, engines={'html': jinja2.TemplateEngine})

def environment(env, data, next_handler):
    env.cfg = cfg

    env.url_for = url_for
    env.url_for_static = static.construct_reverse()
    env.template = template
    env.db = db_maker()
    env.cache = memcache_client

    try:
        return next_handler(env, data)
    finally:
        env.db.close()

app = web.handler(environment) | web.cases(
    auth.login_handler | h.render_to('login.html'),
    auth.logout_handler,
    # API
    match('/api/posts', 'api-posts') | web.cases(
        ctype(ctype.xml) | h.posts_paginator | h.to_xml,
        ctype(ctype.json) | h.posts_paginator | h.to_json,
    ),
    auth | web.cases(
        match('/', 'posts') | h.posts_paginator | h.render_to('posts.html'),
        match('/<int:id>', 'post') | h.post_by_id | h.render_to('post.html'),
        prefix('/posts') | auth.login_required | web.cases(
            match('/add', 'add-post') | h.post_form | h.render_to('add_post.html'),
            match('/edit/<int:id>', 'edit-post') | h.edit_post | h.render_to('add_post.html'),
            match('/delete/<int:id>', 'del-post') | h.del_post | h.render_to('del_post.html')
        )
    ),
)

url_for = web.Reverse(web.locations(app))
