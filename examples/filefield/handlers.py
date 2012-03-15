# -*- coding: utf-8 -*-

import datetime, os
from webob.exc import HTTPSeeOther

from forms import FileForm, OptionalFileForm
from webob.exc import HTTPSeeOther

from insanities.ext.filefields import time_uid

def prepair_dir():
    dir_ = os.path.join(cfg.MEDIA, 'stored')
    if not os.path.isdir(dir_):
        os.makedirs(dir_)
    return dir_


def list_files(env, data, nxt):
    dir_ = prepair_dir()
    files = os.listdir(dir_)
    form = FileForm(env)
    return env.template.render_to_response('index', {
        'files':files, 
        'url':'/media/stored/', 
        'form':form
    }, env)


def post_file(env, data, nxt):
    dir_ = prepair_dir()
    files = os.listdir(dir_)
    form = FileForm(env)
    url = '/media/stored/'

    if form.accept(env.request.POST, env.request.FILES):
        tmp_file = form.python_data['file']
        if tmp_file and tmp_file.mode == 'temp':
            new_path = os.path.join(dir_, tmp_file.uid)
            os.rename(tmp_file.full_path, new_path)

        raise HTTPSeeOther(location=env.request.url)
    return env.template.render_to_response('index', {
        'files':files, 
        'url':'/media/stored/', 
        'form':form
    }, env)


def delete_files(env, data, next_handler):
    dir_ = os.path.join(env.cfg.MEDIA, 'stored')
    f = env.request.GET.get('filename', '')
    filepath = os.path.join(dir_, f)
    if '/' not in f and os.path.isfile(filepath):
        os.unlink(filepath)
    raise HTTPSeeOther(location=str(env.url_for('files')))
