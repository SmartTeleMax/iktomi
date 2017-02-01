# -*- coding: utf-8 -*-

import logging

import six
import cgi
import re
from . import convs, widgets
from ..utils import cached_property
from collections import OrderedDict
from .perms import FieldPerm

logger = logging.getLogger(__name__)

__all__ = ['BaseField', 'Field', 'FieldBlock', 'FieldSet', 'FieldList', 'FileField']


class BaseField(object):
    '''
    Simple container class which ancestors represents various parts of Form.

    Encapsulates converter, various fields attributes, methods for data 
    access control
    '''

    # obsolete parameters from previous versions
    _obsolete = frozenset(['default', 'get_default', 'template', 'media',
                           'render_type', 'render', 'required'])

    #: :class:`FieldPerm` instance determining field's access permissions.
    #: Can be set by field inheritance or throught constructor.
    perm_getter = FieldPerm()

    # defaults
    #: :class:`Converter` instance determining field's convertation method
    conv = convs.Char()
    #: :class:`Widget` instance determining field's render method
    widget = widgets.TextInput
    #: Unicode label of the field
    label = None
    #: Short description of the field
    hint = None

    help = ''

    def __init__(self, name, conv=None, parent=None, permissions=None, **kwargs):
        if self._obsolete & set(kwargs):
            raise TypeError(
                    'Obsolete parameters are used: {}'.format(
                                list(self._obsolete & set(kwargs))))
        kwargs.update(
            parent=parent,
            name=name,
            conv=(conv or self.conv)(field=self),
            widget=(kwargs.get('widget') or self.widget)(field=self),
        )
        if permissions is not None:
            kwargs['perm_getter'] = FieldPerm(permissions)
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
        '''
        String description of validation error in this field during last accept.

        `None` if there is no error.
        '''
        return self.form.errors.get(self.input_name)

    @property
    def help_message(self):
        return self.help or self.form.get_help(self.input_name)

    @cached_property
    def clean_value(self):
        '''
        Current field's converted value from form's python_data.
        '''
        # XXX cached_property is used only for set initial state
        #     this property should be set every time field data
        #     has been changed, for instance, in accept method
        python_data = self.parent.python_data
        if self.name in python_data:
            return python_data[self.name]
        return self.get_initial()

    @property
    def id(self):
        if self.form.id:
            # We use template names in list to replace, so we must use it here to
            # insure unique IDs.
            return '{}-{}'.format(self.form.id, self.input_name)
        return self.input_name

    def from_python(self, value):
        return self.conv.from_python(value)

    @cached_property
    def permissions(self):
        '''
        Field's access permissions. By default, is filled from perm_getter.
        '''
        return self.perm_getter.get_perms(self)

    @cached_property
    def writable(self):
        return 'w' in self.permissions

    @cached_property
    def readable(self):
        return 'r' in self.permissions

    @cached_property
    def field_names(self):
        return [self.name]

    def load_initial(self, initial, raw_data):
        value = initial.get(self.name, self.get_initial())
        self.set_raw_value(raw_data,
                           self.from_python(value))
        return {self.name: value}

    def __repr__(self):
        args = ', '.join([k+'='+repr(v)
                          for k, v in self._init_kwargs.items()
                          if k not in ['widget', 'conv', 'parent']])
        return '{}({})'.format(self.__class__.__name__, args)


class Field(BaseField):
    '''
    Atomic field
    '''

    conv = convs.Char()
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
            if not isinstance(value, six.string_types):
                self.form.errors[self.input_name] = 'Given value has incompatible type'
                return False
        return True

    def accept(self):
        '''Extracts raw value from form's raw data and passes it to converter'''
        value = self.raw_value
        if not self._check_value_type(value):
            # XXX should this be silent or TypeError?
            value = [] if self.multiple else self._null_value
        self.clean_value = self.conv.accept(value)
        return {self.name: self.clean_value}


class AggregateField(BaseField):

    @property
    def python_data(self):
        '''Representation of aggregate value as dictionary.'''
        try:
            value = self.clean_value
        except LookupError:
            # XXX is this necessary?
            value = self.get_initial()
        return self.from_python(value)


class FieldSet(AggregateField):
    '''
    Container field aggregating a couple of other different fields
    '''
    conv = convs.Converter()
    widget = widgets.FieldSetWidget()
    fields = []

    def __init__(self, name, conv=None, fields=None, **kwargs):
        fields = fields if fields is not None else self.fields
        if kwargs.get('parent'):
            conv = (conv or self.conv)(field=self)
            fields = [field(parent=self) for field in fields]
        kwargs.update(
            name=name,
            conv=conv,
            fields=fields,
        )
        BaseField.__init__(self, **kwargs)

    @property
    def prefix(self):
        return self.input_name+'.'

    def get_field(self, name):
        names = name.split('.', 1)
        for field in self.fields:
            if isinstance(field, FieldBlock):
                result = field.get_field(name)
                if result is not None:
                    return result
            if field.name == names[0]:
                if len(names) > 1:
                    return field.get_field(names[1])
                return field
        return None

    def get_initial(self):
        field_names = sum([x.field_names for x in self.fields], [])
        result = dict((name, self.get_field(name).get_initial())
                      for name in field_names)
        return self.conv.accept(result, silent=True)

    def set_raw_value(self, raw_data, value):
        # fills in raw_data multidict, resulting keys are field's absolute names
        assert isinstance(value, dict), \
                'To set raw value on {!r} need dict, got {!r}'\
                        .format(self.input_name, value)
        if not value:
            # Field set can be optional
            return
        field_names = sum([x.field_names for x in self.fields], [])
        for field_name in field_names:
            subvalue = value[field_name]
            field = self.get_field(field_name)
            field.set_raw_value(raw_data, field.from_python(subvalue))

    def accept(self):
        '''
        Accepts all children fields, collects resulting values into dict and
        passes that dict to converter.

        Returns result of converter as separate value in parent `python_data`
        '''
        result = dict(self.python_data)
        for field in self.fields:
            if field.writable:
                result.update(field.accept())
            else:
                # readonly field
                field.set_raw_value(self.form.raw_data,
                                    field.from_python(result[field.name]))
        self.clean_value = self.conv.accept(result)
        return {self.name: self.clean_value}


class FieldBlock(FieldSet):
    '''
    Anonymous FieldSet, values of one are accepted as they are children 
    of FieldBlock's parent.

    FieldBlock is used to logically organize fields and do validation
    of group of fields without naming that group and without dedicating 
    result of accept to separate object.
    '''

    conv = convs.FieldBlockConv()
    widget = widgets.FieldBlockWidget()
    prefix = ''

    def __init__(self, title, fields=[], **kwargs):
        kwargs.update(
            title=title,
            fields=fields,
        )
        kwargs.setdefault('name', '') # XXX generate unique name
        FieldSet.__init__(self, **kwargs)

    @cached_property
    def prefix(self):
        return self.parent.prefix

    def accept(self):
        '''
        Acts as `Field.accepts` but returns result of every child field 
        as value in parent `python_data`.
        '''
        result = FieldSet.accept(self)
        self.clean_value = result[self.name]
        return self.clean_value

    def load_initial(self, initial, raw_data):
        result = {}
        for field in self.fields:
            result.update(field.load_initial(initial, raw_data))
        return result

    @cached_property
    def field_names(self):
        result = []
        for field in self.fields:
            result += field.field_names
        return result

    @property
    def python_data(self):
        # we need only subfield values in python data
        result = {}
        for field_name in self.field_names:
            if field_name in self.parent.python_data:
                result[field_name] = self.parent.python_data[field_name]
        return result


class FieldList(AggregateField):
    '''
    Container aggregating an ordered set of similar fields
    '''

    order = True
    conv = convs.List()
    widget = widgets.FieldListWidget()
    _digit_re = re.compile('\d+$')

    def __init__(self, name, conv=None, field=Field(None),
                 parent=None, **kwargs):
        if parent:
            conv = (conv or self.conv)(field=self)
            field = field(parent=self)
        kwargs.update(
            parent=parent,
            name=name,
            conv=conv,
            field=field,
        )
        BaseField.__init__(self, **kwargs)

    @property
    def prefix(self):
        # NOTE: There was '-' instead of '.' and get_field('list-1') was broken
        return self.input_name+'.'

    def get_initial(self):
        return []

    def get_field(self, name):
        names = name.split('.', 1)
        if not self._digit_re.match(names[0]):
            # XXX is this needed?
            return None
        field = self.field(name=names[0])
        if len(names) > 1:
            return field.get_field(names[1])
        return field

    @property
    def indices_input_name(self):
        return self.input_name+'-indices'

    def accept(self):
        old = self.python_data
        result = OrderedDict()
        for index in self.form.raw_data.getall(self.indices_input_name):
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
                result.update(field.accept())
        self.clean_value = self.conv.accept(result)
        return {self.name: self.clean_value}

    def set_raw_value(self, raw_data, value):
        indices = []
        for index in range(1, len(value)+1):
            index = str(index)
            subvalue = value[index]
            subfield = self.field(name=index)
            subfield.set_raw_value(raw_data, subfield.from_python(subvalue))
            indices.append(index)
        try:
            del raw_data[self.indices_input_name]
        except KeyError:
            pass
        for index in indices:
            raw_data.add(self.indices_input_name, index)


class FileField(Field):
    '''
    The simpliest file field
    '''

    _null_value = None
    conv = convs.SimpleFile()

    def set_raw_value(self, raw_data, value):
        pass

    def _check_value_type(self, values):
        if not self.multiple:
            values = [values]
        for value in values:
            if not isinstance(value, cgi.FieldStorage) and \
               value and \
               not hasattr(value, 'read'): # XXX is this right?
                self.form.errors[self.input_name] = 'Given value is not file'
                return False
        return True

