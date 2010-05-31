# -*- coding: utf-8 -*-

import sys
from os import path

cur_dir = path.abspath('.')

def rel(*args):
    args = [cur_dir] + list(args)
    return path.join(*args)


TEMPLATES = rel('templates')

STATIC = rel('static')

DATABASES = {
    '':'sqlite+pysqlite:///'+rel('data.db')
}
