# -*- coding: utf-8 -*-

__all__ = ['HtmlUI', 'UiMixin']

from StringIO import StringIO

from ...utils import cached_property
from ..form import Form
from .media import FormMedia
from .widgets import DefaultFormWidget, Widget, TextInput


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
        return self.form_widget.render(form=self.form, ui=self, **vars)

    def render_field(self, field, **kw):
        '''Renders a particular field in the bound form'''
        vars = self.globs.copy()
        vars.update(kw)
        widget = self.widgets[field.resolve_name()]
        return widget.render(field=field, ui=self, **vars)


class UiMixin(object):
    def __init__(self, *args, **kw):
        super(UiMixin, self).__init__(*args, **kw)

    def get_ui(self, rctx, form_template=''):
        form_widget = Widget(template=form_template) if form_template else None
        return HtmlUI(form_widget=form_widget,
                      default=TextInput, 
                      from_fields=True,
                      renderer=rctx.vals.renderer,
                      globs=dict(VALS=rctx.vals,
                                 CONF=rctx.conf,
                                 REQUEST=rctx.request))(self)
