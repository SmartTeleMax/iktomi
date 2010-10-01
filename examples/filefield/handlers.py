# -*- coding: utf-8 -*-

import datetime, os

from forms import FileForm
from insanities.web.http import HttpException
from insanities.forms.ui import HtmlUI

from insanities.ext.filefields import TempUploadedFile, time_uid, StoredFile


def redirect_to(url):
    raise HttpException(303, url=url)


def list_files(rctx):
    dir_ = os.path.join(rctx.conf.MEDIA, 'stored')
    if not os.path.isdir(dir_):
        os.makedirs(dir_)
    files = os.listdir(dir_)
    form = FileForm({})
    ui = HtmlUI(from_fields=True, engine=rctx.vals.jinja_env)
    return dict(files=files, url='/media/stored/', form=form, ui=ui)

def post_file(rctx):
    dir_ = os.path.join(rctx.conf.MEDIA, 'stored')
    result = list_files(rctx)
    form, url = result['form'], result['url']

    if form.accept(rctx.request.POST, rctx.request.FILES):
        tmp_file = form.python_data['file']
        if isinstance(tmp_file, TempUploadedFile):
            filename = time_uid() + tmp_file.ext
            new_value = StoredFile(filename, dir_, url)
            os.rename(tmp_file.full_path, new_value.full_path)
        redirect_to(rctx.vals.url_for('files'))
    #result = dict(result)
    return result


def delete_files(rctx):
    dir_ = os.path.join(rctx.conf.MEDIA, 'stored')
    f = rctx.request.GET.get('filename', '')
    filepath = os.path.join(dir_, f)
    if '/' not in f and os.path.isfile(filepath):
        os.unlink(filepath)
    redirect_to(rctx.vals.url_for('files'))
