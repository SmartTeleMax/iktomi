# -*- coding: utf-8 -*-

from insanities.web import *
from insanities.web.filters import *
from insanities.web.wrappers import *

from insanities.ext.jinja2 import render_to, jinja_env
from insanities.ext.cache import cache_dict
from insanities.ext.auth import CookieAuth
from insanities.ext.sqla import sqla_session
from insanities.utils import conf_to_dict


import cfg
import models
import handlers as h

auth = CookieAuth(models.User.by_credential, models.User.by_id)


env = Conf('', **conf_to_dict(cfg)) | jinja_env() | cache_dict() | sqla_session(cfg.DATABASES[''])


app = env | Map(
    auth.login_handler | render_to('login.html'),
    auth.logout_handler,
    # API
    prefix('/api') | Map(
        ctype(ctype.xml) | match('/posts', 'posts-xml') | h.posts_paginator | h.to_xml,
        ctype(ctype.json) | match('/posts', 'posts-json') | h.posts_paginator | h.to_json,
    ),
    auth | Map(
        match('/', 'posts') | h.posts_paginator | render_to('posts.html'),
        match('/<int:id>', 'post') | h.post_by_id | render_to('post.html'),
        auth.login_required | Map(
            match('/+', 'add-post') | h.post_form | render_to('add_post.html'),
            match('/edit/<int:id>', 'edit-post') | h.edit_post | render_to('add_post.html'),
            match('/delete/<int:id>', 'del-post') | h.del_post | render_to('del_post.html')
        )
    ),
)
