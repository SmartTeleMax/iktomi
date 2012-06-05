# -*- coding: utf-8 -*-

from copy import deepcopy
from ..utils import weakproxy, cached_property
from . import convs
from .media import FormMedia, FormCSSRef, FormJSRef

class Widget(object):

    #: Template to render widget
    template = None
    #: List of :class:`FormMediaAtom<insanities.forms.media.FormMediaAtom>`
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
        assert isinstance(self.field.conv, convs.EnumChoice)

        values = value if self.multiple else [value]
        values = map(unicode, values)
        for choice, label in self.field.conv:
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


class GroupedSelect(Select):

    template = 'widgets/grouped_select'
    classname = 'grouped_select select'
    size = None

    def get_options(self, value):
        assert isinstance(self.field.conv, convs.EnumChoice)
        options = []
        if not self.multiple and (value is None or not self.field.conv.required):
            options = [dict(value='', title=self.null_label,
                            selected=value in (None, ''),
                            is_group=False)]
        values = value if self.multiple else [value]
        values = map(unicode, values)

        # TODO fix tree generation
        _group_items = []
        _group_name = None
        for group, choice, label in self.field.conv:
            choice = unicode(choice)
            if (not group and _group_name) or (_group_name and _group_name != group):
                options.append(dict(is_group=True,
                                    title=_group_name,
                                    options=_group_items[0:]))
                _group_name = None
            if group and group != _group_name:
                _group_name = group
                _group_items = []
            if group:
                _group_items.append(dict(value=choice,
                                         title=label,
                                         selected=(choice in values)))
            else:
                options.append(dict(value=choice,
                                    title=label,
                                    selected=(choice in values),
                                    is_group=False))
        if _group_name:
            options.append(dict(is_group=True,
                                title=_group_name,
                                options=_group_items[0:]))
        return options



class CheckBoxSelect(Select):

    template = 'widgets/select-checkbox'


class CheckBox(Widget):

    render_type = 'checkbox'
    template = 'widgets/checkbox'


class Textarea(Widget):

    template = 'widgets/textarea'


class ReadonlySelect(Select):

    template = 'widgets/readonlyselect'


class CharDisplay(Widget):

    template = 'widgets/span'
    classname = 'chardisplay'
    #: If is True, value is escaped while rendering. 
    #: Passed to template as :obj:`should_escape` variable.
    escape = False
    #: Function converting the value to string.
    getter = staticmethod(lambda v: v)

    def prepare_data(self, value):
        data = Widget.prepare_data(self, value)
        return dict(data,
                    value=self.getter(value),
                    should_escape=self.escape)


class ImageView(Widget):

    template = 'widgets/imageview'
    classname = 'imageview'


class FileInput(Widget):
    '''
    '''
    template = 'widgets/file'

    #def prepare_data(self, value):
    #    data = Widget.prepare_data(self, value)

    #    field = self.field
    #    value = field.parent.python_data.get(field.name, None)
    #    delete = field.form.raw_data.get(field.input_name + '__delete', False)
    #    if value is None:
    #        value = field.parent.initial.get(field.name, None)
    #        if isinstance(value, field.stored_file_cls):
    #            mode = 'existing'
    #        else:
    #            value = None
    #            mode = 'empty'
    #    elif isinstance(value, field.stored_file_cls):
    #        mode = 'existing'
    #    elif isinstance(value, field.temp_file_cls):
    #        mode = 'temp'
    #    else:
    #        assert None
    #    return dict(data, value=value, mode=mode, input_name=self.input_name,
    #                delete=delete, temp_url=self.env.rctx.conf.temp_url,
    #                null=field.null)

class ImageInput(FileInput):
    template = 'widgets/imageinput'

