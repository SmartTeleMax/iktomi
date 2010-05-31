# -*- coding: utf-8 -*-

import datetime
from sqlalchemy.orm.exc import NoResultFound
import models
import forms
from insanities.utils.paginator import ModelPaginator, ChunkedPageRange
from insanities.web.http import HttpException


def redirect_to(url):
    raise HttpException(303, url=url)


def posts_paginator(rctx):
    paginator = ModelPaginator(rctx,
                               rctx.vals.db.query(models.Post),
                               impl=ChunkedPageRange(),
                               limit=3
                               )
    return dict(paginator=paginator)


def post_by_id(rctx, id):
    try:
        post = rctx.vals.db.query(models.Post).filter_by(id=id).one()
    except NoResultFound:
        raise HttpException(404)
    else:
        return dict(post=post)


def post_form(rctx):
    form = forms.PostForm(rctx.vals.form_env)
    if rctx.request.method == 'POST':
        if form.accept(rctx.request.POST):
            data = form.python_data
            data['author'] = rctx.vals.user
            data['date'] = datetime.datetime.now()
            post = models.Post(**data)
            rctx.vals.db.add(post)
            rctx.vals.db.commit()
            redirect_to(rctx.vals.url_for('post', id=post.id))
    return dict(form=form)


def del_post(rctx, id):
    db = rctx.vals.db
    try:
        post = db.query(models.Post).filter_by(id=id).one()
    except NoResultFound:
        raise HttpException(404)
    else:
        if rctx.request.method == 'POST':
            db.delete(post)
            db.commit()
            redirect_to(rctx.vals.url_for('posts'))
        return dict(post=post)


def edit_post(rctx, id):
    db = rctx.vals.db
    try:
        post = db.query(models.Post).filter_by(id=id).one()
    except NoResultFound:
        raise HttpException(404)
    else:
        initial = {}
        for field in forms.PostForm.fields:
            initial[field.name] = getattr(post, field.name, '')
        form = forms.PostForm(rctx.vals.form_env, initial=initial)
        if rctx.request.method == 'POST':
            if form.accept(rctx.request.POST):
                data = form.python_data
                data['date'] = datetime.datetime.now()
                post = models.Post(**data)
                rctx.vals.db.add(post)
                rctx.vals.db.commit()
                redirect_to(rctx.vals.url_for('post', id=post.id))
    return dict(form=form)
