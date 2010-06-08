# -*- coding: utf-8 -*-

from os.path import dirname, abspath, join
import logging
logger = logging.getLogger(__name__)

from jinja2 import Environment, FileSystemLoader
from insanities.forms.form import BaseFormEnvironment
from insanities.web.core import RequestHandler

__all__ = ('FormEnvironment', 'render_to', 'jinja_env')

CURDIR = dirname(abspath(__file__))
DEFAULT_TEMPLATE_DIR = join(CURDIR, 'templates')


class FormEnvironment(BaseFormEnvironment):
    '''
    Encapsulates all data and methods needed to form in current realization.

    FormEnvironment should contain template rendering wrapper methods.
    Also it may contain any other stuff used in particular project's forms.
    '''
    def __init__(self, env, rctx=None, globals={}, locals={}):
        self.env = env
        self.rctx = rctx
        self.globals = globals
        self.locals = locals

    def get_template(self, template):
        return self.env.get_template('%s.html' % template,
                                           globals=self.globals)

    def render(self, template, **kwargs):
        vars = dict(self.locals, **kwargs)
        return self.get_template(template).render(**vars)


class render_to(RequestHandler):

    def __init__(self, template=None, param=None, **kwargs):
        assert template or param
        super(render_to, self).__init__()
        self.template = template
        self.param = param
        self._kwargs = kwargs

    def handle(self, rctx):
        template = self.template or rctx.data[self.param]
        if isinstance(template, basestring):
            template = rctx.vals.jinja_env.get_template(template)

        template_kw = self._kwargs.copy()
        template_kw['rctx'] = rctx
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
                 FormEnvCls=FormEnvironment, extensions=None):
        self.param = param
        self.paths = paths
        self.autoescape = autoescape
        self.env = None
        self.extensions = extensions or []
        # form rendering is not the only thing FormEnvironment does.
        # so we need a way to redefine other methods of it (i.e. i18n)
        self.FormEnvCls = FormEnvCls

    def handle(self, rctx):
        kw = rctx.conf.as_dict()
        kw['rctx'] = rctx
        # lazy jinja env
        if self.env is None:
            # paths from init
            paths_list = self._paths_list(self.paths)
            # paths from rctx.conf
            paths_list += self._paths_list(kw.get(self.param))
            # default templates for forms
            paths_list.append(DEFAULT_TEMPLATE_DIR)
            self.env = Environment(
                loader=FileSystemLoader(paths_list),
                autoescape=self.autoescape,
                extensions=self.extensions,
            )
        form_env = self.FormEnvCls(env=self.env, **kw)
        rctx.vals.update(dict(form_env=form_env, jinja_env=self.env))
        return rctx.next()

    def _paths_list(self, paths):
        paths_ = []
        if paths:
            if isinstance(paths, basestring):
                paths_.append(paths)
            elif isinstance(paths, (list, tuple)):
                paths_ += paths
        return paths_
