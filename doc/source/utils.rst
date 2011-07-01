.. _insanities-utils:

Various utilities
=================

Template
--------

.. _insanities-templates:

`insanities.templates.Template` class is originnaly designed to unify 
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
            return self.engine.get_template(template_name).render(kw)

For correct form rendering, an env.template value should be defined::

    from insanities.templates import jinja2, Template

    template = Template(cfg.TEMPLATES,
                        engines={'html': jinja2.TemplateEngine,
                                 'my': MyEngine})

    def environment(env, data, next_handler):
        ...
        env.template = template
        ...
        return next_handler(env, data)

    app = web.handler(environment) | app   

Utils
-----

