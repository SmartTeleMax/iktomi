# -*- coding: utf-8 -*-

__all__ = ['HtmlUI']

from StringIO import StringIO

from ...utils import cached_property
from ..form import Form
from .media import FormMedia
from .widgets import DefaultFormWidget


class HtmlUI(object):
    '''A configuration stateless object of form rendering'''

    def __init__(self, **kw):
        '''
        form_widget - widget which will be rendered, if appears.
        fields_widgets - dict [field_name:widget] which will be used to render field.
        default - widget, default widget if other is absent.
        renderer - template engine (jinja2, mint, ...).
        engine_ext - template files extensions.
        '''
        self.form_widget = kw.get('form_widget')
        self.fields_widgets = kw.get('fields_widgets', {})
        self.default = kw.get('default')
        self.renderer = kw.get('renderer')
        self._init_kw = kw

    def collect_widgets(self, fields):
        widgets = {}
        for field in fields:
            fieldname = field.resolve_name()
            if hasattr(field, 'fields'):
                subwidgets = self.collect_widgets(field.fields)
                widgets.update(subwidgets)
            widget = self.fields_widgets.get(fieldname)
            if not widget:
                widget = getattr(field, 'widget', self.default)
            widgets[fieldname] = widget(renderer=self.renderer)
        return widgets

    def bind(self, renderer):
        'Creates new HtmlUI instance bound to renderer'
        vars = dict(self._init_kw, renderer=renderer)
        return self.__class__(**vars)

    def __call__(self, form):
        '''Binds UI to a form'''
        widgets = self.collect_widgets(form.fields)

        form_widget = self.form_widget or getattr(form, 'widget', 
                                                  DefaultFormWidget)
        form_widget = form_widget(renderer=self.renderer)
        return Renderrer(form, form_widget, widgets, 
                         globs=self._init_kw.get('globs'))


class Renderrer(object):
    '''Stores widgets to render individual fields'''
    def __init__(self, form, form_widget, widgets, globs=None):
        self.widgets = widgets
        self.form = form
        self.form_widget = form_widget
        self.globs = globs or {}

    @cached_property
    def media(self):
        '''Collected FormMedia from form's widgets'''
        media = FormMedia()
        for w in self.widgets.values():
            media += w.get_media()
        return media

    def ui_for(self, field):
        return self.widgets.get(field.resolve_name())

    def render(self):
        '''Renders the form'''
        vars = self.globs.copy()
        vars['form'] = self.form
        vars['ui'] = self
        return self.form_widget.render(**vars)

    def render_field(self, field):
        '''Renders a particular field in the bound form'''
        widget = self.widgets[field.resolve_name()]
        vars = self.globs.copy()
        vars['field'] = field
        vars['ui'] = self
        return widget.render(**vars)
