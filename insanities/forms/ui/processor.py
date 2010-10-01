# -*- coding: utf-8 -*-

__all__ = ['HtmlUI']

from StringIO import StringIO

from ...utils import cached_property
from ..form import Form
from .media import FormMedia
from .widgets import DefaultFormWidget


class HtmlUI(object):

    def __init__(self, **kw):
        '''
        form_widget - widget which will be rendered, if appears.
        fields_widgets - dict [field_name:widget] which will be used to render field.
        default - widget, default widget if other is absent.
        engine - template engine (jinja2, mint, ...).
        engine_ext - template files extensions.
        '''
        self.form_widget = kw.get('form_widget')
        self.fields_widgets = kw.get('fields_widgets', {})
        self.default = kw.get('default')
        engine = kw.get('engine')
        if engine:
            engine = engine_wrapper(engine, ext=kw.get('engine_ext', 'html'))
        self.engine = engine
        self._init_kw = kw

    def collect_widgets(self, fields):
        widgets = {}
        for field in fields:
            fieldname = field.resolve_name()
            if hasattr(field, 'fields'):
                subwidgets = self.collect_widgets(field.fields)
                widgets.update(subwidgets)
            widget = self.fields_widgets.get(fieldname)
            widget = getattr(field, 'widget', self.default)
            widgets[fieldname] = widget(engine=self.engine)
        return widgets

    def bind(self, engine, ext='html'):
        'Creates new HtmlUI instance binded to engine'
        vars = dict(self._init_kw, engine=engine, engine_ext=ext)
        return self.__class__(**vars)

    def render(self, form):
        widgets = self.collect_widgets(form.fields)

        form_widget = self.form_widget or getattr(form, 'widget', DefaultFormWidget)
        form_widget = form_widget(engine=self.engine)
        return _Renderrer(form, form_widget, widgets)


class _Renderrer(object):
    '''Stores widgets to render individual fields'''
    def __init__(self, form, form_widget, widgets):
        self.widgets = widgets
        self.form = form
        self.form_widget = form_widget

    @cached_property
    def media(self):
        media = FormMedia()
        for w in self.widgets.values():
            media += w.get_media()
        return media

    def render(self):
        return self.form_widget.render(form=self.form, ui=self)
    __unicode__ = __html__ = render

    def render_field(self, field):
        widget = self.widgets[field.resolve_name()]
        return widget.render(field=field, ui=self)


class engine_wrapper(object):
    'This wrapper is temporary, for use only with jinja2 or mint'
    def __init__(self, env, ext='html'):
        self.env = env
        self.ext = ext

    def render(self, template_name, **data):
        return self.env.get_template('%s.%s' % (template_name, self.ext)).render(**data)

