# -*- coding: utf-8 -*-

from os.path import dirname, abspath, join
import logging
logger = logging.getLogger(__name__)

from jinja2 import Environment, FileSystemLoader
from insanities.web.core import ContinueRoute, RequestHandler

__all__ = ('FormEnvironment', 'render_to', 'JinjaEnv')

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

    def gettext(self, msg, args={}):
        if isinstance(msg, M_):
            return self.nget_string(msg, msg.plural, args[msg.multiple_by])
        return msg

    def ngetext(self, single, plural, count):
        try:
            if int(msg.multiple_by) !=  1:
                return msg.plural
        except ValueError:
            pass
        return msg


class render_to(RequestHandler):

    def __init__(self, template, **kwargs):
        self.template = template
        self._kwargs = kwargs

    def handle(self, rctx):
        # XXX in handler?
        template = self.template
        if isinstance(template, basestring):
            template = rctx.data['jinja_env'].get_template(template)

        template_kw = dict(rctx.data, rctx=rctx, url_for=rctx.url_for, **self._kwargs)
        logger.debug('render_to - rendering template "%s"' % self.template)
        rendered = template.render(**template_kw)
        rctx.response.write(rendered)
        return rctx


class JinjaEnv(RequestHandler):

    def __init__(self, paths=None, autoescape=False, EnvCls=FormEnvironment):
        paths_ = [DEFAULT_TEMPLATE_DIR]
        if paths:
            if isinstance(paths, basestring):
                paths_.append(paths)
            elif isinstance(paths_, (list, tuple)):
                paths_ += paths
        self.EnvCls = EnvCls
        self.jinja_env = Environment(
            loader=FileSystemLoader(paths_),
            autoescape=autoescape,
        )

    def handle(self, rctx):
        form_env = self.EnvCls(env=self.jinja_env)
        rctx.add_data(form_env=form_env, jinja_env=self.jinja_env)
        raise ContinueRoute(self)
