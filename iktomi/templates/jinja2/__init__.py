# -*- coding: utf-8 -*-

from os.path import dirname, abspath, join
import logging
logger = logging.getLogger(__name__)

import jinja2

__all__ = ('TemplateEngine', 'TEMPLATE_DIR')

CURDIR = dirname(abspath(__file__))
TEMPLATE_DIR = join(CURDIR, 'templates')


class TemplateEngine(object):
    '''
    Jinja2 engine adapter.
    '''
    def __init__(self, paths, cache=False, extensions=None):
        '''
        :param paths: list of paths
        :param extensions: list of extensions
        '''
        self.extensions = extensions or []
        self.env = self._make_env(paths)


    def _make_env(self, paths):
        # XXX make an interface method
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(paths),
            autoescape=True,
            extensions=self.extensions
        )

    def render(self, template_name, **kw):
        'Interface method called from `Template.render`'
        return self.env.get_template(template_name).render(**kw)
