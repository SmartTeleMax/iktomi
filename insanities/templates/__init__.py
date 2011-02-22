# -*- coding: utf-8 -*-

import os
import logging
logger = logging.getLogger(__name__)
from glob import glob
from ..web import Response

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
        logger.debug('Rendering template "%s"' % template_name)
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
        raise TemplateError('Template or engine for template "%s" not found. Dirs %r' % \
                            (pattern, self.dirs))

    def render_to(self, template_name):
        'WebHandler'
        def wrapper(env, data, next_handler):
            data.env = env
            return Response(self.render(template_name, **data.as_dict()))
        return wrapper

    def render_to_response(self, template_name, data, content_type='text/html'):
        'handy method'
        return Response(self.render(template_name, **data),
                        content_type=content_type)
