# -*- coding: utf-8 -*-

__all__ = ['HtmlUI']

from StringIO import StringIO
from .media import FormMedia


def collect_widgets(fields, update, default=None, from_fields=False, engine=None):
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
            widgets[field.resolve_name()] = widget(element=field, engine=engine)
    return widgets


class HtmlUI(object):

    def __init__(self, **kw):
        '''
        form_widget - widget which will be rendered, if appears.
        fields_widgets - dict [field_name:widget] which will be used to render field.
        from_fields - bool make HtmlUI take widgets from fields.
        default - widget, default widget if other is absent.
        engine - template engine (jinja2, mint, ...).
        engine_ext - template files extensions.
        '''
        self.form_widget = kw.get('form_widget')
        self.fields_widgets = kw.get('fields_widgets', {})
        self.from_fields = kw.get('from_fields')
        self.default = kw.get('default')
        engine = kw.get('engine')
        if engine:
            engine = engine_wrapper(engine, ext=kw.get('engine_ext', 'html'))
        self.engine = engine
        self.media = FormMedia()
        self._init_kw = kw

    def collect_widgets(self, form_instance):
        widgets = collect_widgets(form_instance.fields, self.fields_widgets, 
                                  default=self.default, from_fields=self.from_fields,
                                  engine=engine)
        for w in widgets.values():
            self.media += w.get_media()
        return widgets

    def bind(self, engine, ext='html'):
        'Creates new HtmlUI instance binded to engine'
        vars = dict(self._init_kw, engine=engine, engine_ext=ext)
        return self.__class__(**vars)

    def render(self, form):
        form_widget = self.form_widget or getattr(form, widget)
        if form_widget:
            return form_widget.render(form=form, ui=self)
        result = StringIO()
        widgets = self.collect_widgets(form)
        for field in form.fields:
            widget = widgets.get(field.resolve_name())
            if widget:
                result.write(widget.render(field=field, ui=self))
        return result.getvalue()


class engine_wrapper(object):
    def __init__(self, env, ext='html'):
        self.env = env
        self.ext = ext

    def render(self, template_name, **data):
        return self.env.get_template('%s.%s' % (template_name, self.ext)).render(**data)

