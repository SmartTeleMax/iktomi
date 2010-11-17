# -*- coding: utf-8 -*-

import os
import logging
logger = logging.getLogger(__name__)
from glob import glob

from ..web import RequestHandler


__all__ = ('Template',)


class TemplateError(Exception): pass


class Template(object):
    def __init__(self, *dirs, **kwargs):
        self.globs = kwargs.get('globs', {})
        self.cache = kwargs.get('cache', False)
        self.dirs = []
        for d in dirs:
            self.dirs.append(d)
        self.engines = {}
        for template_type, engine_class in kwargs.get('engines', {}).items():
            self.engines[template_type] = engine_class(self.dirs[:], cache=self.cache)

    def render(self, template_name, **kw):
        vars = self.globs.copy()
        vars.update(kw)
        resolved_name, engine = self.resolve(template_name)
        return engine.render(resolved_name, **vars)

    def resolve(self, template_name):
        pattern = template_name
        if not os.path.splitext(template_name)[1]:
            pattern += '.*'
        for d in self.dirs:
            path = os.path.join(d, pattern)
            for file_name in glob(path):
                name, ext = os.path.splitext(file_name)
                template_type = ext[1:]
                if template_type in self.engines:
                    return file_name[len(d)+1:], self.engines[template_type]
        raise TemplateError('Template or engine for template "%s" not found' % pattern)

    def render_to(self, template_name):
        return RenderWrapper(template_name, self)


class RenderWrapper(RequestHandler):
    def __init__(self, template_name, template):
        self.template_name = template_name
        self.template = template
    def handle(self, rctx):
        logger.debug('Rendering template "%s"' % self.template_name)
        template_kw = rctx.data.as_dict()
        template_kw['REQUEST'] = rctx.request
        template_kw['VALS'] = rctx.vals
        template_kw['CONF'] = rctx.conf
        rendered = self.template.render(self.template_name, 
                                        **template_kw)
        rctx.response.write(rendered)
        return rctx.next()
