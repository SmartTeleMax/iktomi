Template
========

`iktomi.templates.Template` class is originnaly designed to unify 
template interface for forms, but can be used in anywhere else.

`Template` object provides `render`, `render_to_response` methods
and `render_to` handler factory. The constructor accepts a list of
directories for search temlates in (as \*args) and following keyworg
arguments:

    - `globs`.
    - `cache`.
    - `engines`.

Engine is class providing `render` method, which accepts template name
and template arguments as keyword args, and returns rendered string.
The constructor shoul accept templates paths list and option switching
template cache on/off::

    class MyEngine(object):
        def __init__(self, paths, cache=False):
            self.engine = MyTemplateEngine(paths, cache=cache)

        def render(self, template_name, **kw):
            template = self.engine.get_template(template_name)
            return template.render(kw)

Iktomi supports `jinja2` engine by default.

Now we can instantiate `Template` object with engines we have::

    from iktomi.templates import jinja2, Template
    from iktomi import web

    jinja_loader = jinja2.TemplateEngine(cfg.TEMPLATES,
                                         extensions=[])
    template = Template(engines={'html': jinja_loader,
                                 'my': MyEngine},
                        *cfg.TEMPLATES)

To bound a template object to the iktomi `env`, to add request-specific 
values to template variables, `BoundTemplate` is used::

    class BoundTemplate(BaseBoundTemplate):

        constant_template_vars = dict(template_vars)

        def get_template_vars(self):
            lang = self.env.lang
            d = dict(
                lang = self.env.lang,
                url = self.env.root,
                url_for_object = self.env.url_for_object,
                url_for_static = self.env.url_for_static,
                now = datetime.now(),
            )
            return d

It is recommended to put it into `env.template` object. Particularly, this is 
required for correct form rendering. And it may be useful to define 
`env.render_to_string` and `env.render_to_response` shortcuts::

    class MyAppEnvironment(web.AppEnvironment):

        # ...

        @storage_cached_property
        def template(storage):
            return BoundTemplate(storage, template_loader)

        @storage_method
        def render_to_string(storage, template_name, _data, *args, **kwargs):
            _data = dict(storage.template_data, **_data)
            result = storage.template.render(template_name, _data, *args, **kwargs)
            return Markup(result)

        @storage_method
        def render_to_response(self, template_name, _data,
                               content_type="text/html"):
            _data = dict(self.template_data, **_data)
            return self.template.render_to_response(template_name, _data,
                                                    content_type=content_type)
