# -*- coding: utf-8 -*-

from os.path import dirname, abspath, join
import logging
logger = logging.getLogger(__name__)

from mint import Loader
from insanities.forms.form import BaseFormEnvironment
from insanities.web.core import RequestHandler

__all__ = ('FormEnvironment', 'render_to', 'mint_env')


class FormEnvironment(BaseFormEnvironment):
    '''
    Encapsulates all data and methods needed to form in current implementation.

    FormEnvironment should contain template rendering wrapper methods.
    Also it may contain any other stuff used in particular project's forms.
    '''
    def __init__(self, rctx, locals=None, **kw):
        self.rctx = rctx #weakproxy(rctx)
        self.locals = locals or {}
        self._init_kw = kw
        self.__dict__.update(kw) # XXX ???

    def get_template(self, template):
        return self.rctx.vals.mint_env.get_template('%s.mint' % template)

    def render(self, template, **kwargs):
        vars = dict(self.locals, **kwargs)
        vars.update(dict(VALS=self.rctx.vals,
                         CONF=self.rctx.conf,
                         REQUEST=self.rctx.request))
        return self.get_template(template).render(**vars)

    def __call__(self, **kwargs):
        kw = self._init_kw.copy()
        kw.update(kwargs)
        return FormEnvironment(self.rctx, **kw)


class render_to(RequestHandler):

    def __init__(self, template=None, param=None, **kwargs):
        assert template or param
        self.template = template
        self.param = param
        self._kwargs = kwargs

    def get_template(self, rctx):
        template = self.template or rctx.data[self.param]
        if isinstance(template, basestring):
            template = rctx.vals.mint_env.get_template(template)
        return template

    def handle(self, rctx):
        template = self.get_template(rctx)

        template_kw = self._kwargs.copy()
        template_kw.update(rctx.data.as_dict())
        logger.debug('mint rendering template "%s"' % self.template)
        rendered = template.render(**template_kw)
        rctx.response.write(rendered)
        return rctx.next()


class mint_env(RequestHandler):
    '''
    This handler adds mint Loader.
    '''

    def __init__(self, param='TEMPLATES', paths=None, cache=True):
        self.param = param
        self.paths = paths
        self.env = None
        self.cache = cache

    def handle(self, rctx):
        if self.env is None:
            self.env = Loader(rctx.conf.TEMPLATES, cache=self.cache, 
                              globals=dict(
                                  VALS=rctx.vals,
                                  CONF=rctx.conf,
                                  REQUEST=rctx.request))
        rctx.vals.update(dict(mint_env=self.env))
        return rctx.next()
