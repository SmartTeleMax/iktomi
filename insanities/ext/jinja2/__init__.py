# -*- coding: utf-8 -*-

from os.path import dirname, abspath, join
import logging
logger = logging.getLogger(__name__)
from ...utils import weakproxy

from jinja2 import Environment, FileSystemLoader
from insanities.forms.form import BaseFormEnvironment
from insanities.web.core import RequestHandler

__all__ = ('render_to', 'jinja_env')

CURDIR = dirname(abspath(__file__))
DEFAULT_TEMPLATE_DIR = join(CURDIR, 'templates')


class render_to(RequestHandler):

    def __init__(self, template=None, param=None, **kwargs):
        assert template or param
        super(render_to, self).__init__()
        self.template = template
        self.param = param
        self._kwargs = kwargs

    def get_template(self, rctx):
        template = self.template or rctx.data[self.param]
        if isinstance(template, basestring):
            template = rctx.vals.jinja_env.get_template(template)
        return template

    def handle(self, rctx):
        template = self.get_template(rctx)

        template_kw = self._kwargs.copy()
        template_kw['VALS'] = rctx.vals.as_dict()
        template_kw['CONF'] = rctx.conf.as_dict()
        template_kw['REQUEST'] = rctx.request
        template_kw.update(rctx.data.as_dict())
        logger.debug('render_to - rendering template "%s"' % self.template)
        rendered = template.render(**template_kw)
        rctx.response.write(rendered)
        return rctx.next()


class jinja_env(RequestHandler):
    '''
    This handler adds Jinja Environment.
    '''

    def __init__(self, param='TEMPLATES', paths=None, autoescape=False,
                 extensions=None):
        self.param = param
        self.paths = paths
        self.autoescape = autoescape
        self.env = None
        self.extensions = extensions or []

    def handle(self, rctx):
        # lazy jinja env
        if self.env is None:
            # paths from init
            paths_list = self._paths_list(self.paths)
            # paths from rctx.conf
            paths_list += self._paths_list(rctx.conf.get(self.param))
            # default templates for forms
            paths_list.append(DEFAULT_TEMPLATE_DIR)
            self.env = Environment(
                loader=FileSystemLoader(paths_list),
                autoescape=self.autoescape,
                extensions=self.extensions,
            )
        rctx.vals.update(dict(jinja_env=self.env))
        return rctx.next()

    def _paths_list(self, paths):
        paths_ = []
        if paths:
            if isinstance(paths, basestring):
                paths_.append(paths)
            elif isinstance(paths, (list, tuple)):
                paths_ += paths
        return paths_
