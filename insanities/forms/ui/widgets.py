# -*- coding: utf-8 -*-

from copy import deepcopy
from ...utils import weakproxy, cached_property
from .. import convs
from media import FormMedia, FormCSSRef, FormJSRef


class Widget(object):

    #: Template to render widget
    template = None
    #: List of :class:`FormMediaAtom<insanities.forms.media.FormMediaAtom>`
    #: objects associated with the widget
    media = []
    #: Value of HTML element's *class* attribute
    classname = ''
    label = ''

    def __init__(self, **kwargs):
        self._init_kwargs = kwargs
        self.__dict__.update(kwargs)

    def get_media(self):
        return FormMedia(self.media)

    def prepare_data(self, **kwargs):
        return kwargs

    def render(self, **kwargs):
        '''
        Renders widget to template
        '''
        data = self.prepare_data(**kwargs)
        data['widget'] = self
        return self.engine.render(self.template, **data)

    def __call__(self, **kwargs):
        kwargs = dict(self._init_kwargs, **kwargs)
        return self.__class__(**kwargs)


class TextInput(Widget):

    template = 'widgets/textinput'
    classname = 'textinput'


class HiddenInput(Widget):

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

    def get_options(self, value, field):
        options = []
        if not field.multiple and value is None and not field.conv.required:
            options = [{'value': '',
                        'title': self.null_label,
                        'selected': value in (None, '')}]
        assert isinstance(field.conv, convs.EnumChoice)

        values = value if field.multiple else [value]
        values = map(unicode, values)
        for choice, label in field.conv:
            choice = unicode(choice)
            options.append(dict(value=choice,
                                title=label,
                                selected=(choice in values)))
        return options

    def prepare_data(self, **kwargs):
        field = kwargs['field']
        return dict(kwargs,
                    options=self.get_options(field.value, field),
                    multiple='multiple' if field.multiple else '',
                    readonly='readonly' if 'w' not in field.permissions else '',
                    required=('true' if field.conv.required else 'false'))


class CheckBoxSelect(Select):

    template = 'widgets/select-checkbox'


class CheckBox(Widget):

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

    def prepare_data(self, **data):
        return dict(data,
                    value=self.getter(value),
                    should_escape=self.escape)


class ImageView(Widget):

    template = 'widgets/imageview'
    classname = 'imageview'


class FileInput(Widget):
    '''
    '''
    template = 'widgets/fileinput'

    def prepare_data(self, **data):
        field = self.field
        value = field.value
        delete = field.form.data.get(field.input_name + '__delete', False)
        if value is None:
            value = field.parent.initial.get(field.name, None)
            if isinstance(value, field.stored_file_cls):
                mode = 'existing'
            else:
                value = None
                mode = 'empty'
        elif isinstance(value, field.stored_file_cls):
            mode = 'existing'
        elif isinstance(value, field.temp_file_cls):
            mode = 'temp'
        else:
            assert None
        return dict(data, value=value, mode=mode, input_name=self.input_name,
                    delete=delete, temp_url=self.env.rctx.conf.temp_url,
                    null=field.null)


class ImageInput(FileInput):
    template = 'widgets/imageinput'

