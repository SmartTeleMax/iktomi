# -*- coding: utf-8 -*-

from ..utils import weakproxy
from . import convs
from .media import FormMedia, FormCSSRef, FormJSRef

class Widget(object):

    #: Template to render widget
    template = None
    #: List of :class:`FormMediaAtom<iktomi.forms.media.FormMediaAtom>`
    #: objects associated with the widget
    media = []
    #: Value of HTML element's *class* attribute
    classname = ''
    #: describes how the widget is rendered.
    #: the following values are supported by default:
    #: 'default': label is rendered in usual place
    #: 'checkbox': label and widget are rendered close to each other
    #: 'full-width': for table-like templates, otherwise should be rendered as default
    #: 'hidden': label is not rendered
    render_type = 'default'

    def __init__(self, field=None, **kwargs):
        self.field = weakproxy(field)
        self._init_kwargs = kwargs
        self.__dict__.update(kwargs)

    @property
    def multiple(self):
        return self.field.multiple

    @property
    def input_name(self):
        return self.field.input_name

    @property
    def id(self):
        return self.field.id

    @property
    def env(self):
        return self.field.env

    def get_media(self):
        return FormMedia(self.media)

    def prepare_data(self, value):
        '''
        Method returning data passed to template.
        Subclasses can override it.
        '''
        return dict(widget=self,
                    value=value,
                    readonly=not self.field.writable)

    def render(self, value):
        '''
        Renders widget to template
        '''
        data = self.prepare_data(value)
        if self.field.readable:
            return self.env.template.render(self.template, **data)
        return ''

    def __call__(self, **kwargs):
        kwargs = dict(self._init_kwargs, **kwargs)
        kwargs.setdefault('field', self.field)
        return self.__class__(**kwargs)


class TextInput(Widget):

    template = 'widgets/textinput'
    classname = 'textinput'


class Textarea(Widget):

    template = 'widgets/textarea'


class HiddenInput(Widget):

    render_type = 'hidden'
    template = 'widgets/hiddeninput'


class PasswordInput(Widget):

    template = 'widgets/passwordinput'
    classname = 'textinput'


class Select(Widget):
    '''
    Takes options from :class:`EnumChoice<EnumChoice>` converter,
    looks up if converter allows null and passed this value as template
    :obj:`required` variable.
    '''
    template = 'widgets/select'
    classname = 'select'
    #: HTML select element's select attribute value.
    size = None
    #: Label assigned to None value if field is not required
    null_label = '--------'

    def get_options(self, value):
        options = []
        if not self.multiple and (value is None or not self.field.conv.required):
            options = [{'value': '',
                        'title': self.null_label,
                        'selected': value in (None, '')}]
        # XXX ugly
        choice_conv = self.field.conv
        if isinstance(choice_conv, convs.ListOf):
            choice_conv = choice_conv.conv
        assert isinstance(choice_conv, convs.EnumChoice)

        values = value if self.multiple else [value]
        values = map(unicode, values)
        for choice, label in choice_conv.options():
            choice = unicode(choice)
            options.append(dict(value=choice,
                                title=label,
                                selected=(choice in values)))
        return options

    def prepare_data(self, value):
        data = Widget.prepare_data(self, value)
        return dict(data,
                    options=self.get_options(value),
                    required=('true' if self.field.conv.required else 'false'))


class CheckBoxSelect(Select):

    template = 'widgets/select-checkbox'


class CheckBox(Widget):

    render_type = 'checkbox'
    template = 'widgets/checkbox'


class CharDisplay(Widget):

    template = 'widgets/span'
    classname = 'chardisplay'
    #: If is True, value is escaped while rendering. 
    #: Passed to template as :obj:`should_escape` variable.
    escape = True
    #: Function converting the value to string.
    getter = staticmethod(lambda v: v)

    def prepare_data(self, value):
        data = Widget.prepare_data(self, value)
        return dict(data,
                    value=self.getter(value),
                    should_escape=self.escape)


class FileInput(Widget):

    template = 'widgets/file'

