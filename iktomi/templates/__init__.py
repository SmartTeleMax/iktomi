# -*- coding: utf-8 -*-

import os
import logging
logger = logging.getLogger(__name__)
from glob import glob
from ..web import Response, request_filter
from ..utils import cached_property

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
        for template_type, engine in kwargs.get('engines', {}).items():
            self.engines[template_type] = engine

    def render(self, template_name, **kw):
        logger.debug('Rendering template "%s"', template_name)
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


class BoundTemplate(object):
    '''
    Usage:
        template = Template(...) # global var

        def environment(env, data, nxt):
            ...
            env.template = BoundTemplate(env, template)
    '''

    def __init__(self, env, template):
        self.template = template
        self.env = env

    def get_template_vars(self):
        return {}

    @cached_property
    def engines(self):
        return self.template.engines

    def _vars(self, __data, **kw):
        if hasattr(__data, 'as_dict'):
            d = __data.as_dict()
        elif __data is not None:
            d = dict(__data)
        else:
            d = {}
        d.update(kw)
        d.update(self.get_template_vars())
        return d

    def render(self, template_name, __data=None, **kw):
        return self.template.render(template_name,
                                    **self._vars(__data, **kw))

    def render_to_response(self, template_name, __data, content_type="text/html"):
        resp = self.render(template_name, __data)
        return Response(resp,
                        content_type=content_type)


def render_to(self, template_name):
    @request_filter
    def render_to(env, data, next_handler):
        data.env = env
        return Response(env.template.render(template_name, **data))
    return render_to

