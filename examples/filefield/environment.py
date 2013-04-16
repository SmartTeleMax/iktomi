# -*- coding: utf-8 -*-

import logging
from iktomi import web
from iktomi.templates import Template, BoundTemplate as BaseBoundTemplate
from iktomi.templates.jinja2 import TemplateEngine
from iktomi.utils.storage import storage_cached_property
from iktomi.utils import cached_property
#from jinja2 import Markup

import cfg


logger = logging.getLogger(__name__)

static = web.static_files('static')
jinja_loader = TemplateEngine(cfg.TEMPLATES)
template_loader = Template(engines={'html': jinja_loader},
                           *cfg.TEMPLATES)

class Environment(web.AppEnvironment):
    cfg = cfg

    @cached_property
    def url_for(self):
        return self.root.build_url

    @cached_property
    def url_for_static(self):
        return static.construct_reverse()

    @storage_cached_property
    def template(storage):
        return BoundTemplate(storage, template_loader)


class BoundTemplate(BaseBoundTemplate):

    def get_template_vars(self):
        d = {}
        #d.update(template_functions)
        d.update(dict(
            env = self.env,
            root = self.env.root,
            url_for = self.env.url_for,
            url_for_static = self.env.url_for_static,
        ))
        return d

    #def render(self, template_name, __data=None, **kw):
    #    r = BaseBoundTemplate.render(self, template_name, __data, **kw)
    #    return Markup(r)



