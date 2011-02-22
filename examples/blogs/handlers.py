# -*- coding: utf-8 -*-

import datetime
from sqlalchemy.orm.exc import NoResultFound
import models
import forms
from insanities.utils.paginator import ModelPaginator, ChunkedPageRange

from webob.exc import HTTPSeeOther, HTTPNotFound
from insanities.web import Response


def render_to(template_name):
    def handler(env, data, next_handler):
        template_data = data.as_dict()
        template_data.update(
            auth_user=env.user,
            url_for=env.url_for,
            url_for_static=env.url_for_static)
        return env.template.render_to_response(template_name, template_data)
    return handler


def posts_paginator(env, data, next_handler):
    data.paginator = ModelPaginator(env.request,
                               env.db.query(models.Post),
                               impl=ChunkedPageRange(),
                               limit=3)
    return next_handler(env, data)


def post_by_id(env, data, next_handler):
    try:
        post = env.db.query(models.Post).filter_by(id=data.id).one()
    except NoResultFound:
        raise HTTPNotFound()
    else:
        return next_handler(env, data(post=post))


def post_form(env, data, next_handler):
    form = forms.PostForm(env)
    if env.request.method == 'POST':
        if form.accept(env.request.POST):
            data = form.python_data
            data['author'] = env.user
            data['date'] = datetime.datetime.now()
            post = models.Post(**data)
            env.db.add(post)
            env.db.commit()
            raise HTTPSeeOther(location=str(env.url_for('post', id=post.id)))
    return next_handler(env, data(form=form))


def del_post(env, data, next_handler):
    try:
        post = env.db.query(models.Post).filter_by(id=data.id).one()
    except NoResultFound:
        raise HTTPNotFound()
    else:
        if env.request.method == 'POST':
            env.db.delete(post)
            env.db.commit()
            raise HTTPSeeOther(location=str(env.url_for('posts')))
        return next_handler(env, data(post=post))


def edit_post(env, data, next_handler):
    try:
        post = env.db.query(models.Post).filter_by(id=data.id).one()
    except NoResultFound:
        raise HTTPNotFound
    else:
        initial = {}
        for field in forms.PostForm.fields:
            initial[field.name] = getattr(post, field.name, '')
        form = forms.PostForm(env, initial=initial)
        if env.request.method == 'POST':
            if form.accept(env.request.POST):
                data = form.python_data
                data['date'] = datetime.datetime.now()
                post = models.Post(**data)
                env.db.add(post)
                env.db.commit()
                raise HTTPSeeOther(location=str(env.url_for('post', id=post.id)))
    return next_handler(env, data(form=form))


from xml.etree.ElementTree import Element, tostring


def to_xml(env, data, next_handler):
    root = Element('posts', {'total_pages': str(data.paginator.pages_count),
                             'page': str(data.paginator.page)})
    for i in data.paginator.items:
        post = Element('post', {'id':str(i.id), 'date':i.date.strftime('%d:%m:%Y')})
        title = Element('title')
        title.text = i.title
        post.append(title)
        body = Element('body')
        body.text = i.body
        post.append(body)
        root.append(post)
    return Response(tostring(root), content_type='application/xml')


import simplejson


def to_json(env, data, next_handler):
    items = [dict(title=i.title,
                  body=i.body,
                  id=i.id,
                  date=i.date.strftime('%d:%m:%Y'))
             for i in data.paginator.items]

    result = simplejson.dumps(
        dict(total_pages=data.paginator.pages_count,
             page=data.paginator.page,
             items=items))
    return Response(result, content_type='application/json')

