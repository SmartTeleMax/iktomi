# -*- coding: utf-8 -*-

from os.path import dirname, abspath, join
import logging
logger = logging.getLogger(__name__)

from jinja2 import Environment, FileSystemLoader
from insanities.web.core import ContinueRoute, RequestHandler, Wrapper

__all__ = ('FormEnvironment', 'render_to', 'jinja_env')

CURDIR = dirname(abspath(__file__))
DEFAULT_TEMPLATE_DIR = join(CURDIR, 'templates')


class FormEnvironment(object):
    '''
    Encapsulates all data and methods needed to form in current realization.

    FormEnvironment should contain template rendering wrapper methods.
    Also it may contain any other stuff used in particular project's forms.
    '''
    def __init__(self, env, rctx=None, globals={}, locals={}, **kwargs):
        self.env = env
        self.rctx = rctx
        self.globals = globals
        self.locals = locals
        self.__dict__.update(kwargs)

    def get_template(self, template):
        return self.env.get_template('%s.html' % template,
                                           globals=self.globals)

    def render(self, template, **kwargs):
        vars = dict(self.locals, **kwargs)
        return self.get_template(template).render(**vars)


class render_to(RequestHandler):

    def __init__(self, template, **kwargs):
        super(render_to, self).__init__()
        self.template = template
        self._kwargs = kwargs

    def handle(self, rctx):
        template = self.template
        if isinstance(template, basestring):
            template = rctx.vals.jinja_env.get_template(template)

        template_kw = self._kwargs.copy()
        template_kw['rctx'] = rctx
        template_kw.update(rctx.data.as_dict())
        logger.debug('render_to - rendering template "%s"' % self.template)
        rendered = template.render(**template_kw)
        rctx.response.write(rendered)
        return rctx


class jinja_env(Wrapper):

    def __init__(self, param='TEMPLATES', autoescape=False):
        super(jinja_env, self).__init__()
        self.param = param
        self.autoescape = autoescape

    def handle(self, rctx):
        kw = rctx.conf.as_dict()
        kw['rctx'] = rctx
        paths = kw.pop(self.param, None)
        paths_ = []
        if paths:
            if isinstance(paths, basestring):
                paths_.append(paths)
            elif isinstance(paths, (list, tuple)):
                paths_ += paths
        paths_.append(DEFAULT_TEMPLATE_DIR)
        jinja_env = Environment(
            loader=FileSystemLoader(paths_),
            autoescape=self.autoescape,
        )
        form_env = FormEnvironment(env=jinja_env, **kw)
        rctx.vals.update(dict(form_env=form_env, jinja_env=jinja_env))
        rctx = self.exec_wrapped(rctx)
        return rctx
