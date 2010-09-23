# -*- coding: utf-8 -*-

from StringIO import StringIO


def collect_widgets(fields, update, default=None, from_fields=False):
    widgets = {}
    for field in fields:
        if from_fields and hasattr(field, 'widget'):
            widgets[field.resolve_name()] = field.widget
        if hasattr(field, 'fields'):
            widgets.update(collect_widgets(field.fields, update))
        if default:
            widgets[field.resolve_name()] = update.get(field.resolve_name(), default)
        elif field.resolve_name() in update:
            widgets[field.resolve_name()] = update.get(field.resolve_name())
    return widgets


class HtmlUI(object):

    def __init__(self, form, form_widget=None, default=None, fields=None, from_fields=False):
        self.form = form
        self.form_widget = form_widget
        fields = fields or {}
        self.widgets = collect_widgets(form.fields, fields, default=default, from_fields=from_fields)

    def render(self):
        if self.form_widget:
            return self.form_widget.render(form=self.form, ui=self)
        result = StringIO()
        for field in self.form.fields:
            widget = self.widgets.get(field.resolve_name())
            if widget:
                result.write(widget.render(field=field, ui=self))

    def css(self):
        pass

    def js(self):
        pass
