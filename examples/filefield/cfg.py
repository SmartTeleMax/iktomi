# -*- coding: utf-8 -*-

from os import path
from iktomi.templates import jinja2 as jnj2

cur_dir = path.abspath('.')
IKTOMI_FORMS_DIR = path.dirname(path.abspath(jnj2.__file__))

def rel(*args):
    args = [cur_dir] + list(args)
    return path.join(*args)


TEMPLATES = [rel('templates'),
             path.join(IKTOMI_FORMS_DIR, 'templates')]

STATIC = rel('static')
MEDIA = rel('media')

