# -*- coding: utf-8 -*-

from ..utils import weakproxy
from . import convs


class Widget(object):

    # obsolete parameters from previous versions
    _obsolete = frozenset(['multiple'])

    #: Template to render widget
    template = None
    #: Value of HTML element's *class* attribute
    classname = ''
    #: describes how the widget is rendered.
    #: the following values are supported by default:
    #: 'default': label is rendered in usual place
    #: 'checkbox': label and widget are rendered close to each other
    #: 'full-width': for table-like templates, otherwise should be rendered as default
    #: 'hidden': label is not rendered
    render_type = 'default'
    #: True if widget renders hint itself.
    #: Otherwise parent field should render the hint
    renders_hint = False

    def __init__(self, field=None, **kwargs):
        if self._obsolete & set(kwargs):
            raise TypeError(
                    'Obsolete parameters are used: {}'.format(
                                list(self._obsolete & set(kwargs))))
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

    def prepare_data(self):
        '''
        Method returning data passed to template.
        Subclasses can override it.
        '''
        value = self.get_raw_value()
        return dict(widget=self,
                    field=self.field,
                    value=value,
                    readonly=not self.field.writable)

    def get_raw_value(self):
        return self.field.raw_value

    def render(self):
        '''
        Renders widget to template
        '''
        data = self.prepare_data()
        if self.field.readable:
            return self.env.template.render(self.template, **data)
        return ''

    def __call__(self, **kwargs):
        '''
        Creates current object's copy with extra constructor arguments passed.
        '''
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
    classname = None
    #: HTML select element's select attribute value.
    size = None
    #: Label assigned to None value if field is not required
    null_label = '--------'

    def get_options(self, value):
        options = []

        # XXX ugly
        choice_conv = self.field.conv
        if isinstance(choice_conv, convs.ListOf):
            choice_conv = choice_conv.conv
        assert isinstance(choice_conv, convs.EnumChoice)

        has_null_value = False

        values = value if self.multiple else [value]
        for choice, label in choice_conv.options():
            has_null_value = has_null_value or choice == ''
            options.append(dict(value=choice,
                                title=label,
                                selected=(choice in values)))

        if not self.multiple and not has_null_value and \
                (value == '' or not self.field.conv.required) and \
                self.null_label is not None:
            options.insert(0, {'value': '',
                               'title': self.null_label,
                               'selected': value in (None, '')})
        return options

    def prepare_data(self):
        data = Widget.prepare_data(self)
        return dict(data,
                    options=self.get_options(data['value']),
                    required=('true' if self.field.conv.required else 'false'))


class CheckBoxSelect(Select):

    classname = 'select-checkbox'
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

    def prepare_data(self):
        data = Widget.prepare_data(self)
        return dict(data,
                    value=self.getter(data['value']),
                    should_escape=self.escape)


class AggregateWidget(Widget):

    def get_raw_value(self):
        return None


class FieldListWidget(AggregateWidget):

    allow_create = True
    allow_delete = True

    template = 'widgets/fieldlist'

    def render_template_field(self):
        # used in iktomi.cms: templates/widgets/fieldlist.html
        field = self.field.field(name='%'+self.field.input_name+'-index%')
        # XXX looks like a HACK
        field.set_raw_value(self.field.form.raw_data,
                            field.from_python(field.get_initial()))
        return field.widget.render()


class FieldSetWidget(AggregateWidget):

    template = 'widgets/fieldset'


class FieldBlockWidget(FieldSetWidget):

    render_type = 'full-width'


class FileInput(Widget):

    template = 'widgets/file'

