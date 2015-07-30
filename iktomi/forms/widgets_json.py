# -*- coding: utf-8 -*-

from . import convs
from .widgets import Widget
from iktomi.utils import cached_property
from jinja2 import Markup


class Widget(Widget):

    @cached_property
    def widget_name(self):
        return type(self).__name__

    def render(self):
        props = dict(widget=self.widget_name,
                     key=self.field.name,
                     renders_hint=self.renders_hint,
                     render_type=self.render_type,
                     label=unicode(self.field.label or ''),
                     hint=unicode(self.field.hint or ''),
                     safe_label=isinstance(self.field.label, Markup),
                     safe_hint=isinstance(self.field.hint, Markup),
                     readonly=not self.field.writable,
                     #id=self.field.id,
                     #input_name=self.field.input_name,
                     required=self.field.conv.required,
                     multiple=self.multiple,
                     classname=self.classname)
        if hasattr(self.field, 'initial'):
            props['initial'] = self.field.initial
        return props


class TextInput(Widget):

    classname = 'textinput'


class Textarea(Widget):
    pass


class HiddenInput(Widget):

    render_type = 'hidden'


class PasswordInput(Widget):

    classname = 'textinput'


class Select(Widget):
    classname = None
    #: HTML select element's select attribute value.
    size = None
    #: Label assigned to None value if field is not required
    null_label = '--------'

    def get_options(self):
        options = []
        # XXX ugly
        choice_conv = self.field.conv
        if isinstance(choice_conv, convs.ListOf):
            choice_conv = choice_conv.conv
        assert isinstance(choice_conv, convs.EnumChoice)

        for choice, label in choice_conv.options():
            options.append(dict(value=unicode(choice),
                                title=label))
        return options

    def render(self):
        return dict(super(Select, self).render(),
                    size=self.size,
                    null_label=self.null_label,
                    options=self.get_options())


class CheckBoxSelect(Select):

    classname = 'select-checkbox'


class CheckBox(Widget):

    render_type = 'checkbox'

    def render(self):
        checked = self.field.get_data()[self.field.name]
        return dict(Widget.render(self),
                    checked=checked)



class CharDisplay(Widget):

    classname = 'chardisplay'
    #: If is True, value is escaped while rendering. 
    #: Passed to template as :obj:`should_escape` variable.
    escape = True
    #: Function converting the value to string.
    getter = staticmethod(lambda v: v)

    def render(self):
        value = self.field.clean_value
        return dict(super(CharDisplay, self).render(),
                    value=self.getter(value),
                    should_escape=self.escape)


class FieldListWidget(Widget):

    sortable = True

    def render(self):
        subfield = self.field.field(parent=self.field)
        return dict(Widget.render(self),
                    subwidget=subfield.widget.render(),
                    sortable=self.sortable)


class FieldSetWidget(Widget):

    def render(self):
        widgets = [x.widget.render() for x in
                   self.field.fields]
        return dict(super(FieldSetWidget, self).render(),
                    widgets=widgets)


class FieldBlockWidget(FieldSetWidget):

    # TODO: add unique name to prevent component key collision
    render_type = 'full-width'


class FileInput(Widget):
    pass
