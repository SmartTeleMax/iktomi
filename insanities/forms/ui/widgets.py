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


class FieldWidget(Widget):

    def render(self, field=None, **kwargs):
        kwargs['value'] = field.grab()
        return Widget.render(self, field=field, **kwargs)


class TextInput(FieldWidget):

    template = 'widgets/textinput'
    classname = 'textinput'


class HiddenInput(FieldWidget):

    template = 'widgets/hiddeninput'


class PasswordInput(FieldWidget):

    template = 'widgets/passwordinput'
    classname = 'textinput'


class Select(FieldWidget):
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
        if not field.multiple and (value is None or not field.conv.required):
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


class CheckBox(FieldWidget):

    template = 'widgets/checkbox'


class Textarea(FieldWidget):

    template = 'widgets/textarea'


class ReadonlySelect(Select):

    template = 'widgets/readonlyselect'


class CharDisplay(FieldWidget):

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


class ImageView(FieldWidget):

    template = 'widgets/imageview'
    classname = 'imageview'


class FileInput(Widget):
    '''
    '''
    template = 'widgets/fileinput'

    def prepare_data(self, field=None, **data):
        value = field.value
        delete = field.get_field('delete').value
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
        return dict(data, field=field, value=value, mode=mode,
                    temp_url=field.conv.temp_url,
                    required=field.required)


class ImageInput(FileInput):
    template = 'widgets/imageinput'


class FieldSetWidget(Widget):

    template = 'fields/fieldset'


class FieldListWidget(Widget):

    template = 'fields/fieldlist'


class FormWidget(Widget):

    template = 'forms/table'

