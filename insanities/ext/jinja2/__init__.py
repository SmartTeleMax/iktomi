# -*- coding: utf-8 -*-

from os.path import dirname, abspath, join
import logging
logger = logging.getLogger(__name__)

import jinja2

__all__ = ('TemplateEngine',)

CURDIR = dirname(abspath(__file__))
DEFAULT_TEMPLATE_DIR = join(CURDIR, 'templates')


class TemplateEngine(object):
    def __init__(self, paths=None, autoescape=False,
                 extensions=None):
        '''
        paths - list of paths or str path
        '''
        paths = paths if isinstance(paths, (list, tuple)) else [paths]
        # default templates for forms widgets
        paths.append(DEFAULT_TEMPLATE_DIR)
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(paths),
            autoescape=autoescape,
            extensions=extensions or [],
        )

    def render(self, template_name, **kw):
        'Interface method'
        return self.env.get_template(template_name).render(**kw)
