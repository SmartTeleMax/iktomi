# -*- coding: utf-8 -*-

from StringIO import StringIO


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

    def __init__(self, form_class, form_widget=None, default=None, fields_widgets=None, from_fields=False):
        self.form_widget = form_widget
        fields_widgets = fields_widgets or {}
        self.widgets = collect_widgets(form_class.fields, fields_widgets, default=default, from_fields=from_fields)
        self.media = FormMedia()
        for w in self.widgets.values():
            self.media += FormMedia(w.media)

    def render(self, form):
        if self.form_widget:
            return self.form_widget.render(form=form, ui=self)
        result = StringIO()
        for field in form.fields:
            widget = self.widgets.get(field.resolve_name())
            if widget:
                result.write(widget.render(field=field, ui=self))
        return result.getvalue()
