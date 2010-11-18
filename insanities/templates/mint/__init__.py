# -*- coding: utf-8 -*-

from os.path import dirname, abspath, join
import logging
logger = logging.getLogger(__name__)

import mint

__all__ = ('TemplateEngine', 'TEMPLATE_DIR')

CURDIR = dirname(abspath(__file__))
TEMPLATE_DIR = join(CURDIR, 'templates')


class TemplateEngine(object):
    def __init__(self, paths, cache=False):
        '''
        paths - list of paths
        '''
        self.env = mint.Loader(*paths, cache=cache)

    def render(self, template_name, **kw):
        'Interface method'
        return self.env.get_template(template_name).render(**kw)

    def render_string(self, source, **kw):
        'Interface method'
        return mint.Template(source=source).render(**kw)
