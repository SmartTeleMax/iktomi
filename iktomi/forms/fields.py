# -*- coding: utf-8 -*-

import logging

import cgi
import re
import widgets
from . import convs
from ..utils import cached_property
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

    @property
    def render_type(self):
        return self.widget.render_type

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
    _null_value = ''

    def get_initial(self):
        if hasattr(self, 'initial'):
            return self.initial
        if self.multiple:
            return []
        return None

    @property
    def raw_value(self):
        if self.multiple:
            return self.form.raw_data.getall(self.input_name)
        else:
            return self.form.raw_data.get(self.input_name, '')

    def set_raw_value(self, raw_data, value):
        if self.multiple:
            try:
                del raw_data[self.input_name]
            except KeyError:
                pass
            for v in value:
                raw_data.add(self.input_name, v)
        else:
            raw_data[self.input_name] = value

    def _check_value_type(self, values):
        if not self.multiple:
            values = [values]
        for value in values:
            if not isinstance(value, basestring):
                self.form.errors[self.input_name] = 'Given value has incompatible type'
                return False
        return True

    def accept(self):
        value = self.raw_value
        if not self._check_value_type(value):
            value = [] if self.multiple else self._null_value
        return self.conv.accept(value)


class AggregateField(BaseField):

    @property
    def python_data(self):
        '''Representation of aggregate value as dictionary.'''
        try:
            value = self.clean_value
        except LookupError:
            value = self.get_initial()
        return self.from_python(value)


class FieldSet(AggregateField):
    '''
    Container field aggregating a couple of other different fields
    '''
    template = 'widgets/fieldset'
    render_type = 'default'
    conv = convs.Converter

    def __init__(self, name, conv=None, fields=[], **kwargs):
        if kwargs.get('parent'):
            conv = (conv or self.conv)(field=self)
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

    def get_initial(self):
        result = dict((field.name, field.get_initial())
                      for field in self.fields)
        return self.conv.accept(result, silent=True)

    def set_raw_value(self, raw_data, value):
        # fills in raw_data multidict, resulting keys are field's absolute names
        assert isinstance(value, dict), 'To set raw value need dict, got %r' % value
        for field in self.fields:
            subvalue = value[field.name]
            field.set_raw_value(raw_data, field.from_python(subvalue))

    def accept(self):
        result = dict(self.python_data)
        for field in self.fields:
            if field.writable:
                result[field.name] = field.accept()
            else:
                # readonly field
                field.set_raw_value(self.form.raw_data,
                                    field.from_python(result[field.name]))
        return self.conv.accept(result)

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
    template = 'widgets/fieldlist'
    render_type = 'default'
    conv = convs.List
    _digit_re = re.compile('\d+$')

    def __init__(self, name, conv=None, field=Field(None),
                 parent=None, **kwargs):
        if parent:
            conv = (conv or self.conv)(field=self)
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
        return self.input_name+'.'

    def get_initial(self):
        return []

    def get_field(self, name):
        names = name.split('.', 1)
        if not self._digit_re.match(names[0]):
            return None
        field = self.field(name=names[0])
        if len(names) > 1:
            return field.get_field(names[1])
        return field

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
        return self.conv.accept(result)

    def set_raw_value(self, raw_data, value):
        indeces = []
        for index in range(1, len(value)+1):
            index = str(index)
            subvalue = value[index]
            subfield = self.field(name=index)
            subfield.set_raw_value(raw_data, subfield.from_python(subvalue))
            indeces.append(index)
        if self.indeces_input_name in self.form.raw_data:
            del self.form.raw_data[self.indeces_input_name]
        for index in indeces:
            self.form.raw_data.add(self.indeces_input_name, index)

    def render(self):
        return self.env.template.render(self.template, field=self)

    def get_media(self):
        media = BaseField.get_media(self)
        media += self.field.get_media()
        return media


class FileField(Field):
    '''
    The simpliest file field
    '''

    _null_value = None

    def get_default(self):
        return None # XXX

    def set_raw_value(self, raw_data, value):
        pass

    def _check_value_type(self, values):
        if not self.multiple:
            values = [values]
        for value in values:
            if value and \
               not isinstance(value, cgi.FieldStorage) and \
               not hasattr(value, 'read'): # XXX is this right?
                self.form.errors[self.input_name] = 'Given value is not file'
                return False
        return True


