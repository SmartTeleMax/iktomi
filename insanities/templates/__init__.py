# -*- coding: utf-8 -*-

from os import path
import logging
logger = logging.getLogger(__name__)

from ..web import RequestHandler


__all__ = ('Template',)


class Template(object):
    def __init__(self, cfg, by_ext=None, by_dir=None, 
                 default=None, globs=None):
        self.globs = globs or {}
        self.by_ext = by_ext if by_ext else {}
        self.by_dir = by_dir if by_dir else {}
        self.default_renderer = default
        self.cfg = cfg

    def render(self, template_name, **kw):
        vars = self.globs.copy()
        vars.update(kw)
        for dir_prefix, renderer in self.by_dir.items():
            if template_name.startswith(dir_prefix):
                return self.by_dir[dir_prefix].render(template_name, **vars)
        name, ext = path.splitext(template_name)
        if ext:
            ext = ext[1:]
            if ext in self.by_ext:
                return self.by_ext[ext].render(template_name, **vars)
        else:
            for ext, renderer in self.by_ext.items():
                #TODO: improve this code, it is not working for cases
                #      where cfg.TEMPLATES is a list of dirs or
                #      for dirs outside of cfg.TEMPLATES
                p = path.abspath(path.join(self.cfg.TEMPLATES, 
                                           '%s.%s' % (template_name, ext)))
                if path.exists(p) and path.isfile(p):
                    return renderer.render('%s.%s' % (template_name, ext),
                                           **vars)
        if self.default_renderer:
            return self.default_renderer.render(template_name, **vars)
        raise Exception('Template object has no renderer for "%s"' % template_name)

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
