# -*- coding: utf-8 -*-

from os.path import dirname, abspath, join
import logging
logger = logging.getLogger(__name__)

import jinja2

__all__ = ('TemplateEngine', 'TEMPLATE_DIR')

CURDIR = dirname(abspath(__file__))
TEMPLATE_DIR = join(CURDIR, 'templates')


class TemplateEngine(object):
    def __init__(self, paths, cache=False):
        '''
        paths - list of paths
        '''
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(paths),
            autoescape=True,
        )

    def render(self, template_name, **kw):
        'Interface method'
        return self.env.get_template(template_name).render(**kw)
