# -*- coding: utf-8 -*-

from os.path import dirname, abspath, join
import logging
logger = logging.getLogger(__name__)

from mint import Loader
from insanities.forms.form import BaseFormEnvironment
from insanities.web.core import RequestHandler

__all__ = ('render_to', 'mint_env')


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

    def __init__(self, param='TEMPLATES', paths=None, cache=True, globals=None):
        self.param = param
        self.paths = paths
        self.env = None
        self.cache = cache
        self.globals = globals or {}

    def handle(self, rctx):
        if self.env is None:
            gl=dict(
                VALS=rctx.vals,
                CONF=rctx.conf,
                REQUEST=rctx.request)
            gl.update(self.globals)
            self.env = Loader(rctx.conf.TEMPLATES, cache=self.cache, 
                              globals=gl)
        rctx.vals.update(dict(mint_env=self.env))
        return rctx.next()
