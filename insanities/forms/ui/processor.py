# -*- coding: utf-8 -*-

__all__ = ['HtmlUI']

from StringIO import StringIO
from .media import FormMedia


def collect_widgets(fields, update, default=None, from_fields=False):
    widgets = {}
    for field in fields:
        if hasattr(field, 'fields'):
            widgets.update(collect_widgets(field.fields, update))
            continue
        widget = None
        if from_fields and hasattr(field, 'widget'):
            widget = field.widget
        else:
            widget = update.get(field.resolve_name(), default)
        if widget:
            widgets[field.resolve_name()] = widget(element=field)
    return widgets


class HtmlUI(object):

    def __init__(self, form_widget=None, default=None, fields_widgets=None, from_fields=False, engine=None):
        self.form_widget = form_widget
        self.fields_widgets = fields_widgets or {}
        self.media = FormMedia()
        self.from_fields = from_fields
        self.default = default
        self.engine = engine

    def collect_widgets(self, form_instance):
        widgets = collect_widgets(form_instance.fields, self.fields_widgets, 
                                  default=self.default, from_fields=self.from_fields)
        for w in widgets.values():
            self.media += w.get_media()
        return widgets

    def bind(self, engine, ext='html'):
        self.env = engine_wrapper(engine, ext=ext)
        return self

    def render(self, form):
        if self.form_widget:
            return self.form_widget.render(form=form, ui=self)
        result = StringIO()
        widgets = self.collect_widgets(form)
        for field in form.fields:
            widget = widgets.get(field.resolve_name())
            if widget:
                result.write(widget(env=self.env).render(field=field, ui=self))
        return result.getvalue()


class engine_wrapper(object):
    def __init__(self, env, ext='html'):
        self.env = env
        self.ext = ext

    def render(self, template_name, **data):
        return self.env.get_template('%s.%s' % (template_name, self.ext)).render(**data)
