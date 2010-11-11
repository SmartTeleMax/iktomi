# -*- coding: utf-8 -*-

from ..utils import weakproxy, cached_property
from . import convs
from ..utils.odict import OrderedDict
import re, logging
from .perms import FieldPerm

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

    # default converter
    conv = convs.Char

    def __init__(self, name, conv=None, parent=None, **kwargs):
        kwargs.update(dict(
            parent=parent,
            name=name,
            conv=(conv or self.conv)(field=self),
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
        '''
        Converts field's raw value to python, but raises SkipReadonly exception
        if there are no write permission to the field.
        '''
        if 'w' not in self.permissions:
            raise convs.SkipReadonly
        return self.to_python(self.raw_value)


class AggregateField(BaseField):

    @property
    def python_data(self):
        '''Representation of aggregate value as dictionary.'''
        try:
            value = self.value
        except LookupError:
            value = self.get_default()
        return self.from_python(value)


class FieldSet(AggregateField):
    '''
    Container field aggregating a couple of other different fields
    '''

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
        try:
            return self.to_python(result)
        except convs.ValidationError:
            #XXX: what?
            assert False, 'FieldSet converter must overwrite get_default() '\
                                            'method when validation is needed'

    def set_raw_value(self, value):
        # fills in raw_data multidict, resulting keys are field's absolute names
        for field in self.fields:
            subvalue = value[field.name]
            field.set_raw_value(field.from_python(subvalue))

    def accept(self):
        if 'w' not in self.permissions:
            raise convs.SkipReadonly
        result = self.python_data
        is_valid = True
        for field in self.fields:
            try:
                result[field.name] = field.accept()
            except convs.ValidationError, e:
                is_valid = False
                self.form.errors[field.input_name] = e.message
            except convs.NestedError:
                is_valid = False
            except convs.SkipReadonly:
                field.set_raw_value(field.from_python(result[field.name]))
        if not is_valid:
            raise convs.NestedError
        return self.to_python(result)


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
        if 'w' not in self.permissions:
            raise convs.SkipReadonly
        old = self.python_data
        is_valid = True
        result = OrderedDict()
        for index in self.form.data.getall(self.indeces_input_name):
            try:
                index = int(index)
            except ValueError:
                logger.warning('Got incorrect index from form: %r', index)
                continue
            field = self.field(name=str(index))
            try:
                result[field.name] = field.accept()
            except convs.ValidationError, e:
                is_valid = False
                self.form.errors[field.input_name] = e.message
                if index in old:
                    result[field.name] = old[field.name]
            except convs.NotSubmitted:
                if index in old:
                    result[field.name] = old[field.name]
        if not is_valid:
            raise convs.NestedError
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
