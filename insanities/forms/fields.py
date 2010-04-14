# -*- coding: utf-8 -*-

from ..utils import weakproxy, quote_js, cached_property
from . import convs, widgets
from ..utils.odict import OrderedDict
import re, logging
from .media import FormMedia, FormCSSRef, FormJSRef
from .perms import FieldPerm

logger = logging.getLogger(__name__)


class FieldError(Exception): pass


class BaseField(object):
    '''
    Simple container class which ancestors represents various parts of Form.
    
    Encapsulates converter, various fields attributes, media objects,
    methods for data access control, widget to render the g
    '''

    #: Passed to widget and rendered as HTML element of field's classname.
    #: Can be set by field inheritance or throught constructor.
    classname = None
    #: :class:`FormMedia` incstance containing media objects related to the field.
    #: Can be set by field inheritance or throught constructor.
    media = FormMedia()
    #: :class:`FieldPerm` instance determining field's access permissions.
    #: Can be set by field inheritance or throught constructor.
    perm_getter = FieldPerm()
    

    def __init__(self, **kwargs):
        #if 'label' in kwargs:
        #    kwargs['_label'] = kwargs.pop('label')
        self._init_kwargs = kwargs
        self.__dict__.update(kwargs)

    def __call__(self, **kwargs):
        '''
        Creates current object's copy with extra constructor arguments passed.
        '''
        params = dict(self._init_kwargs, **kwargs)
        return self.__class__(**params)

    def resolve_name(self):
        import form
        name = str(self.name)
        if isinstance(self.parent, form.Form):
            return name
        return self.parent.resolve_name() + '.' + name

    @property
    def label(self):
        '''
        Label of field. Can be set by field inheritance or throught constructor.
        '''
        if 'label' in self.__dict__:
            return self.env.gettext(self.__dict__['label'])
        return None
    
    @property
    def parent(self):
        '''
        Proxy getter of current field's parent. Parent can be Form instance or
        other BaseField instance if there are field nesting.
        
        Raises FormError if it is attempt to access the parent of an unbound
        field.
        '''
        if self.__dict__.get('parent', None):
            return self.__dict__['parent']
        raise FieldError('Field "%s" is unbound' % self.__class__.__name__)

    @property
    def multiple(self):
        '''Proxy property. Checks if field's converter is multiple'''
        return self.conv.multiple

    @property
    def env(self):
        '''Field's form environment'''
        return self.parent.env

    @property
    def form(self):
        '''Field's form'''
        return self.parent.form

    @property
    def input_name(self):
        '''
        Name of field's input element generated in account to possible
        nestiong of fields. The input name is to be used in templates as value
        of Input (Select, etc) element's Name attribute and Label element's For
        attribute.
        
        It is also used as key in form's data multidict.
        
        The property is available only if field is bound.
        '''
        return self.parent.prefix + self.name
    
    @property
    def error(self):
        '''
        Field's error in last validation

        The property is available only if field is bound.
        '''
        return self.form.errors.get(self.input_name)
    
    @property
    def value(self):
        '''
        Current field's converted value from form's python_data.
        '''
        return self.parent.python_data[self.name]

    @cached_property
    def _relative_id(self): # XXX what is this?
        return self.form.get_field_id(self)

    @property
    def id(self):
        '''
        Field's input ID in order of form's ID and field's input name.
        '''
        # We use template names in list to replace, so we must use it here to
        # insure unique IDs.
        return '%s-%s' % (self.form.id, self.input_name)
            
    def to_python(self, value):
        return self.conv.to_python_wrapper(value)
    
    def from_python(self, value):
        return self.conv.from_python(value)
    
    @cached_property
    def permissions(self):
        '''
        Returns field's access permissions
        '''
        return self.perm_getter.get_perms(self)

    def get_media(self):
        return FormMedia(self.media)


class Field(BaseField):
    '''
    Atomic field
    '''

    #: :class:`Widget` class instance used to render the field.
    #: Can be set by Field inheritance or throught constructor.
    widget = None

    def __init__(self, name, conv=convs.Char, widget=widgets.TextInput,
                 parent=None, **kwargs):
        kw = {}
        if parent is not None:
            kw['field'] = self
        conv = conv(**kw)
        widget = widget(**kw)
        
        kwargs.update(dict(
            parent=parent,
            name=name,
            conv=conv,
            widget=widget,
        ))
        BaseField.__init__(self, **kwargs)
    
    def get_default(self):
        '''
        Returns fields default value
        '''
        if hasattr(self, 'default'):
            return self.default
        if self.multiple:
            return []
        return None
    
    def grab(self):
        '''
        Returns field's raw value from form's data multidict.
        '''
        if self.multiple:
            return self.form.data.getall(self.input_name)
        else:
            return self.form.data.get(self.input_name, '')

    def fill(self, data, value):
        '''
        Sets the value in given multidict using field's input_name as key.
        '''
        if self.multiple:
            try:
                del data[self.input_name]
            except KeyError:
                pass
            for v in value:
                data.add(self.input_name, v)
        else:
            data[self.input_name] = value
    
    def accept(self):
        '''
        Converts field's raw value to python, but raises SkipReadonly exception
        if there are no write permission to the field.
        '''
        # XXX Is this an interface method?
        if 'w' not in self.permissions:
            raise convs.SkipReadonly
        return self.to_python(self.grab())

    def get_media(self):
        '''
        Returns a list of field's media objects included ones from field's widget.
        '''
        media = BaseField.get_media(self)
        media += self.widget.get_media()
        return media
    
    def render(self):
        '''
        Renders the field.
        '''
        readonly = 'w' not in self.permissions
        value = self.grab()
        return self.widget.render(value, readonly=readonly)


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

    #: template name used to load fieldset's template and render it.
    #: Can be set by FieldSet inheritance or throught constructor.
    template = 'fieldset'
    media = FormCSSRef('fieldset-line.ccss')

    def __init__(self, name, conv=convs.Converter, fields=[], parent=None,
                 **kwargs):
        if parent is not None:
            conv = conv(field=self)
            fields = [field(parent=self) for field in fields]
        kwargs.update(dict(
            parent=parent,
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
            assert False, 'FieldSet converter must overwrite get_default() '\
                                            'method when validation is needed'

    def fill(self, data, value):
        # fills in data multidict, resulting keys are field's absolute names
        for field in self.fields:
            subvalue = value[field.name]
            field.fill(data, field.from_python(subvalue))

    def accept(self):
        if 'w' not in self.permissions:
            raise convs.SkipReadonly
        result = self.python_data.copy()
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
                field.fill(self.form.data,
                           field.from_python(result[field.name]))
                try:
                    if hasattr(field, 'grab'):
                        field.to_python(field.grab())
                except convs.ValidationError, e:
                    self.form.errors[field.input_name] = e.message
                except convs.NotSubmitted:
                    pass
        if not is_valid:
            raise convs.NestedError
        return self.to_python(result)

    def render(self):
        return self.env.render('fields/'+self.template, field=self)

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
    #: template name used to load fieldlist's template and render it.
    #: Can be set by FieldList inheritance or throught constructor.
    template = 'fieldlist'
    media = [FormJSRef('string.js'),
             FormJSRef('fieldlist.js'),
             FormCSSRef('fieldlist.ccss')]

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

    def fill(self, data, value):
        length = len(value)
        indeces = []
        for index in range(1, length+1):
            index = str(index)
            subvalue = value[index]
            subfield = self.field(name=index)
            subfield.fill(data, subfield.from_python(subvalue))
            indeces.append(index)
        for index in indeces:
            data.add(self.indeces_input_name, index)

    def render(self):
        template = self.field(name='%'+self.input_name+'-index%').render()
        return self.env.render('fields/'+self.template, field=self,
                               encoded_template=quote_js(template))

    def get_media(self):
        media = BaseField.get_media(self)
        media += self.field.get_media()
        return media
