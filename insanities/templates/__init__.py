# -*- coding: utf-8 -*-

from os import path

__all__ = ('Template',)

class Template(object):
    def __init__(self, by_ext=None, by_dir=None, default=None):
        self.by_ext = by_ext if by_ext else {}
        self.by_dir = by_dir if by_dir else {}
        self.default_renderer = default

    def render(self, template_name, **kw):
        for dir_prefix, renderer in self.by_dir.items():
            if template_name.startswith(dir_prefix):
                return self.by_dir[dir_prefix].render(template_name, **kw)
        name, ext = path.splitext(template_name)
        if ext:
            ext = ext[1:]
            if ext in self.by_ext:
                return self.by_ext[ext[1:]].render(template_name, **kw)
        else:
            for ext, renderer in self.by_ext.items():
                p = path.join(template_name, ext)
                if path.exists(p) and path.isfile(p):
                    return renderer.render(p, **kw)
        if self.default_renderer:
            return self.default_renderer.render(template_name, **kw)
        raise Exception('Template object has no renderer for "%s"' % template_name)
