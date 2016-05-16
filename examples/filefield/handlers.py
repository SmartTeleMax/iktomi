# -*- coding: utf-8 -*-

import os
from webob.exc import HTTPSeeOther

from forms import FileForm as FileForm

#from iktomi.ext.filefields import time_uid

def prepair_dir(env):
    dir_ = os.path.join(env.cfg.MEDIA_DIR, 'stored')
    if not os.path.isdir(dir_):
        os.makedirs(dir_)
    return dir_


def list_files(env, data):
    dir_ = prepair_dir(env)
    files = os.listdir(dir_)
    form = FileForm(env)
    return env.template.render_to_response('index', {
        'files':files, 
        'url':'/media/stored/', 
        'form':form
    })


def post_file(env, data):
    dir_ = prepair_dir(env)
    files = os.listdir(dir_)
    form = FileForm(env)

    if form.accept(env.request.POST):
        tmp_file = form.python_data['file']
        if tmp_file is not None:
            new_path = os.path.join(dir_, tmp_file.file_name)
            os.rename(tmp_file.path, new_path)

        raise HTTPSeeOther(location=env.request.url)
    print(form.errors)
    return env.template.render_to_response('index', {
        'files':files, 
        'url':'/media/stored/', 
        'form':form
    })


def delete_files(env, data):
    dir_ = os.path.join(env.cfg.MEDIA_DIR, 'stored')
    f = env.request.GET.get('filename', '')
    filepath = os.path.join(dir_, f)
    if '/' not in f and os.path.isfile(filepath):
        os.unlink(filepath)
    raise HTTPSeeOther(location=str(env.url_for('files')))
