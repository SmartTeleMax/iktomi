# -*- coding: utf-8 -*-

import re, logging

import widgets
from . import convs
from ..utils import weakproxy, cached_property
from ..utils.odict import OrderedDict
from .perms import FieldPerm
from .media import FormMedia

logger = logging.getLogger(__name__)


class BaseField(object):
    '''
    Simple container class which ancestors represents various parts of Form.

    Encapsulates converter, various fields attributes, methods for data 
    access control
    '''

    #: :class:`FieldPerm` instance determining field's access permissions.
    #: Can be set by field inheritance or throught constructor.
    perm_getter = FieldPerm()

    # defaults
    conv = convs.Char
    widget = widgets.TextInput()
    label = None
    media = FormMedia()

    def __init__(self, name, conv=None, parent=None, **kwargs):
        kwargs.update(dict(
            parent=parent,
            name=name,
            conv=(conv or self.conv)(field=self),
            widget=(kwargs.get('widget') or self.widget)(field=self),
        ))
        self._init_kwargs = kwargs
        self.__dict__.update(kwargs)

    def __call__(self, **kwargs):
        '''
        Creates current object's copy with extra constructor arguments passed.
        '''
        params = dict(self._init_kwargs, **kwargs)
        return self.__class__(**params)

    @property
    def multiple(self):
        return self.conv.multiple

    @property
    def env(self):
        return self.parent.env

    @property
    def form(self):
        return self.parent.form

    @property
    def input_name(self):
        '''
        Name of field's input element generated in account to possible
        nesting of fields. The input name is to be used in templates as value
        of Input (Select, etc) element's Name attribute and Label element's For
        attribute.
        '''
        return self.parent.prefix + self.name

    @property
    def error(self):
        return self.form.errors.get(self.input_name)

    @property
    def clean_value(self):
        '''
        Current field's converted value from form's python_data.
        '''
        return self.parent.python_data[self.name]

    @cached_property
    def _relative_id(self): # XXX what is this?
        return self.form.get_field_id(self)

    @property
    def id(self):
        # We use template names in list to replace, so we must use it here to
        # insure unique IDs.
        return '%s-%s' % (self.form.id, self.input_name)

    def to_python(self, value):
        return self.conv.to_python(value)

    def from_python(self, value):
        return self.conv.from_python(value)

    @cached_property
    def permissions(self):
        '''
        Returns field's access permissions
        '''
        return self.perm_getter.get_perms(self)

    @cached_property
    def writable(self):
        return 'w' in self.permissions

    @cached_property
    def readable(self):
        return 'r' in self.permissions

    def render(self):
        return self.widget.render(self.raw_value)

    def get_media(self):
        media = FormMedia(self.media)
        media += self.widget.get_media()
        return media


class Field(BaseField):
    '''
    Atomic field
    '''

    #: :class:`Conv` subclass or instance used to convert field data 
    #: and validate it
    conv = convs.Char

    def get_default(self):
        if hasattr(self, 'default'):
            return self.default
        if self.multiple:
            return []
        return None

    @property
    def raw_value(self):
        if self.multiple:
            return self.form.raw_data.getall(self.input_name)
        else:
            return self.form.raw_data.get(self.input_name, '')

    def set_raw_value(self, value):
        raw_data = self.form.raw_data
        if self.multiple:
            try:
                del raw_data[self.input_name]
            except KeyError:
                pass
            for v in value:
                raw_data.add(self.input_name, v)
        else:
            raw_data[self.input_name] = value

    def accept(self):
        return self.to_python(self.raw_value)


class AggregateField(BaseField):

    @property
    def python_data(self):
        '''Representation of aggregate value as dictionary.'''
        try:
            value = self.clean_value
        except LookupError:
            value = self.get_default()
        return self.from_python(value)


class FieldSet(AggregateField):
    '''
    Container field aggregating a couple of other different fields
    '''
    template = 'widgets/fieldset'
    def __init__(self, name, conv=convs.Converter, fields=[], **kwargs):
        if kwargs.get('parent'):
            conv = conv(field=self)
            fields = [field(parent=self) for field in fields]
        kwargs.update(dict(
            name=name,
            conv=conv,
            fields=fields,
        ))
        BaseField.__init__(self, **kwargs)

    @property
    def prefix(self):
        return self.input_name+'.'

    def get_field(self, name):
        names = name.split('.', 1)
        for field in self.fields:
            if field.name == names[0]:
                if len(names) > 1:
                    return field.get_field(names[1])
                return field
        return None

    def get_default(self):
        result = dict((field.name, field.get_default())
                      for field in self.fields)
        return self.to_python(result)

    def set_raw_value(self, value):
        # fills in raw_data multidict, resulting keys are field's absolute names
        assert isinstance(value, dict), 'To set raw value need dict, got %r' % value
        for field in self.fields:
            subvalue = value[field.name]
            field.set_raw_value(field.from_python(subvalue))

    def accept(self):
        result = self.python_data
        for field in self.fields:
            if field.writable:
                result[field.name] = field.accept()
            else:
                # readonly field
                field.set_raw_value(field.from_python(result[field.name]))
        return self.to_python(result)

    def render(self):
        return self.env.template.render(self.template, field=self)

    def get_media(self):
        media = BaseField.get_media(self)
        for field in self.fields:
            media += field.get_media()
        return media


class FieldList(AggregateField):
    '''
    Container aggregating a couple of similar fields
    '''

    order = False

    def __init__(self, name, conv=convs.List, field=Field(None),
                 parent=None, **kwargs):
        if parent:
            conv = conv(field=self)
            field = field(parent=self)
        kwargs.update(dict(
            parent=parent,
            name=name,
            conv=conv,
            field=field,
        ))
        BaseField.__init__(self, **kwargs)

    @property
    def prefix(self):
        return self.input_name+'-'

    def get_default(self):
        return []

    def get_field(self, name):
        names = name.split('.', 1)
        if self.field.name == names[0] or self.field.name is None:
            if len(names) > 1:
                return self.field.get_field(names[1])
            return self.field
        return None

    @property
    def indeces_input_name(self):
        return self.input_name+'-indeces'

    def accept(self):
        old = self.python_data
        result = OrderedDict()
        for index in self.form.raw_data.getall(self.indeces_input_name):
            try:
                #XXX: we do not convert index to int, just check it.
                #     is it good idea?
                int(index)
            except ValueError:
                logger.warning('Got incorrect index from form: %r', index)
                continue
            #TODO: describe this
            field = self.field(name=str(index))
            if not field.writable:
                # readonly field
                if index in old:
                    result[field.name] = old[field.name]
            else:
                result[field.name] = field.accept()
        return self.to_python(result)

    def set_raw_value(self, value):
        indeces = []
        for index in range(1, len(value)+1):
            index = str(index)
            subvalue = value[index]
            subfield = self.field(name=index)
            subfield.set_raw_value(subfield.from_python(subvalue))
            indeces.append(index)
        for index in indeces:
            self.form.raw_data.add(self.indeces_input_name, index)

    def render(self):
        return self.env.template.render(self.template, field=self)

    def get_media(self):
        media = BaseField.get_media(self)
        media += self.field.get_media()
        return media
