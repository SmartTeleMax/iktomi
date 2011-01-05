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

    template = 'widgets/checkbox'


class Textarea(Widget):

    template = 'widgets/textarea'


class TinyMce(Widget):

    template = 'widgets/tinymce'

    media = [FormJSRef('tiny_mce/tiny_mce_init.js')]

    #: List of buttons used on widget
    buttons = (('bold', 'italic', 'underline'),
               ('bullist', 'numlist'),
               ('sub', 'sup'),
               ('indent', 'outdent'),
               ('link', 'unlink'),
               ('undo', 'redo'),
               ('fullscreen', ))

    #: List of attached plugins
    plugins = ('safari', 'directionality',
               'fullscreen', 'xhtmlxtras', 'inlinepopups')

    #: Need to be documented
    content_css = None

    #: Need to be documented
    browsers = ('safari', 'gecko', 'msie')

    #: TinyMce initial config
    cfg = {
        'mode': 'exact',
        'elements': '%(name)s',
        'theme': 'advanced',
        'browsers': '%(browsers)s',
        'language': 'ru',
        'plugins': '%(plugins)s',
        'height': 200,
        'cleanup': True,
        'valid_elements': '%(tags)s',
        'inline_styles': False,
        'gecko_spellcheck': True,
        'force_p_newlines' : True,
        'paste_auto_cleanup_on_paste': True,
        'remove_redundant_brs': True,
        'fix_table_elements': True,
        'fix_nesting': True,
        'theme_advanced_buttons1': '%(buttons)s',
        'theme_advanced_buttons2': '',
        'theme_advanced_buttons3': '',
        'theme_advanced_buttons4': '',
        'theme_advanced_toolbar_location': 'top',
        'theme_advanced_toolbar_align': 'left',
        'theme_advanced_statusbar_location': 'bottom',
        'theme_advanced_resizing': True,
    }

    #: Need to be documented
    compress = False

    def select_value(self, value, default):
        if value is not None:
            if callable(value):
                return value()
            if type(value) is dict:
                return value.copy()
            return value
        return default

    def __init__(self, add_plugins=None, add_buttons=None, drop_buttons=None,
                 **kwargs):

        for option in 'buttons', 'plugins', 'browsers', 'cfg', 'content_css':
            val = kwargs.get(option, None)
            default = getattr(self, option)
            kwargs[option] = self.select_value(val, default)

        if add_plugins:
            kwargs['plugins'] = tuple(list(kwargs['plugins']) + list(add_plugins))
        if add_buttons or drop_buttons:
            btns = map(list, kwargs['buttons'])
            if add_buttons:
                for row, buttons in add_buttons.items():
                    btns[row].extend(buttons)
            if drop_buttons:
                btns = map(lambda row: filter(lambda b: b not in drop_buttons, row), btns)
                btns = filter(None, btns)
            kwargs['buttons'] = tuple(map(tuple, btns))

        super(TinyMce, self).__init__(**kwargs)

    @cached_property
    def js_config(self):
        '''Serializes all TinyMce configs into JSON object'''
        buttons = ',|,'.join([','.join(pack) for pack in self.buttons])
        plugins = ','.join(self.plugins)
        browsers = ','.join(self.browsers)
        tags = ''
        if hasattr(self.field.conv, 'allowed_attributes') and \
        hasattr(self.field.conv, 'allowed_elements'):
            tags = '@[%s],%s' % ('|'.join(set(self.field.conv.allowed_attributes)),
                                 ','.join(self.field.conv.allowed_elements))
        cfg = self.cfg.copy()
        for key, value in cfg.items():
            if type(value) is str and '%' in value:
                cfg[key] = value % {'buttons': buttons, 'plugins': plugins,
                                    'browsers': browsers, 'tags': tags,
                                    'name': self.id}
        if self.content_css:
            css = self.content_css
            if not css.startswith('/'):
                css = self.env.cfg.STATIC_URL + css
            cfg['content_css'] = css

        cfg['field_name'] = self.field.resolve_name()

        import json
        return json.dumps(cfg)

    def prepare_data(self, value):
        data = Widget.prepare_data(self, value)
        return dict(data,
                    config=self.js_config,
                    plugins=','.join(self.plugins))



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
    template = 'widgets/fileinput'

    def prepare_data(self, value):
        data = Widget.prepare_data(self, value)

        field = self.field
        value = field.parent.python_data.get(field.name, None)
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

