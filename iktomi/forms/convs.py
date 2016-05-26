# -*- coding: utf-8 -*-
'''
Module containing some predefined form converters - objects designed to
convert and validate form field's data.
'''

import six
import re
from ..utils import weakproxy, replace_nontext
from datetime import datetime
from collections import OrderedDict
from ..utils.dt import strftime
from ..utils.deprecation import deprecated
try:
    from ..utils.html import Cleaner
    from lxml import html
    from lxml.etree import XMLSyntaxError
except ImportError: # pragma: no cover
    # lxml is required for Html conv, therefore you can use forms without this
    # functionality
    Cleaner = None

from iktomi.utils import cached_property
from iktomi.utils.i18n import N_, M_
from sqlalchemy.ext.associationproxy import _AssociationCollection


_all2 = set(vars())



class ValidationError(Exception):
    '''
    Error raised from inside of `Converter.to_python` or validator function.

    :param unicode message: error message for current validating
        field, for most cases.
    :param dict by_field: contains {field-name: error message} pairs.
    :param dict format_args: used to format error message.
    '''

    default_message = N_('Something is wrong')

    def __init__(self, message=None, by_field=None, format_args=None):
        if not (message or by_field):
            message = self.default_message
        self.message = message
        self.by_field = by_field or {}
        self.format_args = format_args or {}

    def translate(self, env, message):
        format_args = self.format_args
        if isinstance(message, M_):
            trans = env.ngettext(message.single,
                                 message.plural,
                                 message.count)
            format_args = dict(format_args,
                               **message.format_args)
        else:
            trans = env.gettext(message)
        return trans % format_args

    def fill_errors(self, field):
        form = field.form
        if self.message is not None:
            form.errors[field.input_name] = self.translate(form.env, self.message)
        for name, message in self.by_field.items():
            if name.startswith('.'):
                nm, f = name.lstrip('.'), field
                for i in range(len(name) - len(nm) - 1):
                    f = f.parent
                rel_field = f.get_field(nm)
                name = rel_field.input_name
            else:
                rel_field = form.get_field(name)
            form.errors[name] = self.translate(form.env, message)

    def __repr__(self):
        return "{}({!r}, {!r})".format(self.__class__, self.message,
                                       self.by_field)


class Converter(object):
    '''
    :meth:`accept` method takes value from field
    and converts it to python type.

    Subclasses must redefine :meth:`to_python` method to make their
    own convertation and validation.

    :meth:`from_python` method takes value as python
    object and converts it to string or something
    else widget can display.

    Accepts a list of validators as **\*args**.
    '''

    # obsolete parameters from previous versions
    _obsolete = frozenset(['max_length', 'min_length', 'null', 'min', 'max',
                           'multiple', 'initial'])
    #: Flag of whether perform require check after :meth:`to_python` method or not.
    #: The resulting value is checked to be non-empty (`[]`, `None`).
    required = False
    multiple = False

    #: An ordered list of validator functions. Are passed as position args
    #: to the converter::
    #:
    #:     Int(validator1, validator2)
    #:
    #: When a converter is copied, new validators are added to existing ones.
    validators = ()

    #: Values are not accepted by Required validator
    error_required = N_('required field')

    def __init__(self, *args, **kwargs):
        if self._obsolete & set(kwargs):
            raise TypeError(
                    'Obsolete parameters are used: {}'.format(
                                list(self._obsolete & set(kwargs))))
        self.field = weakproxy(kwargs.get('field'))
        self._init_kwargs = kwargs
        self.__dict__.update(kwargs)
        self.validators = tuple(self.validators) + args

    @property
    def env(self):
        '''A shortcut for `form.env`'''
        return self.field.env

    def _is_empty(self, value):
        return value in ('', [], {}, None)

    def accept(self, value, silent=False):
        '''
        Accepts a value from the form, calls :meth:`to_python` method,
        checks `required` condition, applies filters and validators,
        catches ValidationError.

        :param value: a value to be accepted
        :param silent=False: write errors to `form.errors` or not
        '''
        try:
            value = self.to_python(value)
            for v in self.validators:
                value = v(self, value)

            if self.required and self._is_empty(value):
                raise ValidationError(self.error_required)
        except ValidationError as e:
            if not silent:
                e.fill_errors(self.field)
            #NOTE: by default value for field is in python_data,
            #      but this is not true for FieldList where data
            #      is dynamic, so we set value to None for absent value.
            value = self._existing_value
        return value

    def to_python(self, value):
        """
        Converts value and validates it.
        Custom converters should override this
        """
        if value == '':
            return None # XXX is this right?
        return value

    def from_python(self, value):
        """
        Serializes value.
        Custom converters should override this
        """
        if value is None:
            value = ''
        return value

    def __call__(self, *args, **kwargs):
        '''
        Creates current object's copy with extra constructor arguments
        (including validators) passed.
        '''
        kwargs = dict(self._init_kwargs, **kwargs)
        kwargs.setdefault('field', self.field)
        validators = kwargs.pop('validators', self.validators)
        validators = tuple(validators) + args
        return self.__class__(*validators, **kwargs)

    def assert_(self, expression, msg):
        'Shortcut for assertions of certain type'
        if not expression:
            raise ValidationError(msg)

    @property
    def _existing_value(self):
        if self.field is not None:
            return self.field.parent.python_data.get(self.field.name)
        return [] if self.multiple else None

    def __repr__(self):
        args = ', '.join([k+'='+repr(v) for
                          k, v in self._init_kwargs.items()
                          if k!='parent'])
        return '{}({})'.format(self.__class__.__name__, args)


class validator(object):
    'Function decorator'
    def __init__(self, message):
        self.message = message
    def __call__(self, func):
        def wrapper(conv, value):
            if not func(conv, value):
                raise ValidationError(self.message)
            return value
        return wrapper

# Some useful validators

class length(object):
    'String length constraint'

    func_name = 'check_length' # XXX for backward compatibility

    def __init__(self, min_length, max_length):
        self.min_length = min_length
        self.max_length = max_length

        self.format_args = dict(min=min_length, max=max_length)

        if min_length == max_length:
            self.message = M_(u'length of value must be exactly %(max)d symbol',
                              u'length of value must be exactly %(max)d symbols',
                              count_field="max",
                              format_args=self.format_args)
        else:
            self.message = N_('length should be between %(min)d and %(max)d symbols')

    def __call__(self, conv, value):
        if value and not (self.min_length <= len(value) <= self.max_length):
            raise ValidationError(self.message, format_args=self.format_args)
        return value


@deprecated('Use length(min, max) instead.')
def limit(min_length, max_length):
    return length(min_length, max_length) # pragma: no cover


def between(min_value, max_value):
    'Numerical values limit'
    message = N_('value should be between %(min)d and %(max)d') % \
                    dict(min=min_value, max=max_value)

    @validator(message)
    def wrapper(conv, value):
        if value is None:
            # it meens that this value is not required
            return True
        if value < min_value:
            return False
        if value > max_value:
            return False
        return True
    return wrapper

@deprecated('Use between(min, max) instead.')
def num_limit(min_value, max_value):
    return between(min_value, max_value) # pragma: no cover


class CharBased(Converter):

    nontext_replacement = u'\uFFFD' # Set None to disable and empty string to
                                    # remove.
                                    # Default value is u"�"
    #: Whether strip value before convertation or not
    strip = True

    def clean_value(self, value):
        '''
        Additional clean action to preprocess value before :meth:`to_python`
        method.

        Subclasses may define own clean_value method to allow additional clean
        actions like html cleanup, etc.
        '''
        # We have to clean before checking min/max length. It's done in
        # separate method to allow additional clean action in subclasses.
        if self.nontext_replacement is not None:
            value = replace_nontext(value, self.nontext_replacement)
        if self.strip:
            value = value.strip()
        return value


class Char(CharBased):

    '''Converts and validates strings'''

    #: Regexp to match input string
    regex = None
    #: Error message for the case self.regex does not match
    error_regex = N_('field should match %(regex)s')
    #: Whether strip value before convertation or not
    strip = True

    @property
    def max_length(self):
        length_validators = [x for x in self.validators
                             if isinstance(x, length)]
        if length_validators:
            return min([x.max_length for x in length_validators])
        return None

    def to_python(self, value):
        # converting
        value = self.clean_value(value)
        if value and self.regex:
            regex = self.regex
            if isinstance(regex, six.string_types):
                regex = re.compile(self.regex, re.U)
            if not regex.match(value):
                error = self.error_regex % {'regex': self.regex}
                raise ValidationError(error)
        return value

    def from_python(self, value):
        if value is None:
            return ''
        if six.PY3 and isinstance(value, bytes):
            raise TypeError() # pragma: no cover, safety check
        return six.text_type(value)


class Int(Converter):
    """
    Converts digital sequences to `int`
    """

    #: Error message for the case value can not be converted to int
    error_notvalid = N_('it is not valid integer')

    def to_python(self, value):
        if value == '':
            return None
        try:
            value = int(value)
        except ValueError:
            raise ValidationError(self.error_notvalid)
        return value

    def from_python(self, value):
        if value is None:
            return ''
        return six.text_type(value)


class Bool(Converter):
    """
    Converts to `True`/`False`
    """
    required = False

    def to_python(self, value):
        return bool(value)

    def from_python(self, value):
        if value:
            return 'checked'
        return ''


class EnumChoice(Converter):
    '''
    In addition to Converter interface it must provide
    :meth:`options` and :meth:`get_label` methods.
    '''

    #: converter for value, before it is tested to be in a set of acceptable
    #: values
    conv = Char()

    #: acceptable choices list::
    #:
    #:     EnumChoice(choices=[(python_value, label), ...])
    choices = ()
    error_required = N_('you must select a value')

    def from_python(self, value):
        conv = self.conv
        return conv.from_python(value)

    def to_python(self, value):
        value = self.conv.accept(value, silent=True)
        if value not in dict(self.choices):
            return None
        return value

    def options(self):
        '''
        Yields `(raw_value, label)` pairs for all acceptable choices.
        '''
        conv = self.conv
        for python_value, label in self.choices:
            yield conv.from_python(python_value), label


class BaseDatetime(CharBased):
    '''
    A base class for `Datetime`, `Date` and `Time` converters.
    '''

    #: format used to convert from string by `strptime`
    #: and to convert to string by `strftime`.
    format = None
    #: format used in error message. By default, generated automatically
    #: based `format` and `replacements` attributes
    readable_format = None
    replacements = (('%H', 'HH'), ('%M', 'MM'), ('%d', 'DD'),
                    ('%m', 'MM'), ('%Y', 'YYYY'))
    #: error message for wrong format.
    error_wrong_format = N_('Wrong format (%(readable_format)s)')
    nontext_replacement = ''

    def __init__(self, *args, **kwargs):
        if not 'readable_format' in kwargs or 'format' in kwargs:
            replacements = self.replacements # XXX make language-dependent
            fmt = kwargs.get('format', self.format)
            for repl in replacements:
                fmt = fmt.replace(*repl)
            kwargs['readable_format'] = fmt
        Converter.__init__(self, *args, **kwargs)

    def from_python(self, value):
        if value is None:
            return ''
        # carefull to years before 1900
        return strftime(value, self.format)

    def to_python(self, value):
        value = self.clean_value(value)
        if not value:
            return None
        try:
            return self.convert_datetime(value)
        except ValueError:
            format_args = dict(readable_format=self.readable_format)
            raise ValidationError(self.error_wrong_format,
                                  format_args=format_args)


class Datetime(BaseDatetime):
    '''
    Subclass of `BaseDatetime` for `datetime.datetime`
    '''

    format = '%d.%m.%Y, %H:%M'

    def convert_datetime(self, value):
        return datetime.strptime(value, self.format)


class Date(BaseDatetime):
    '''
    Subclass of `BaseDatetime` for `datetime.date`
    '''

    format = '%d.%m.%Y'

    def convert_datetime(self, value):
        return datetime.strptime(value, self.format).date()


class Time(BaseDatetime):
    '''
    Subclass of `BaseDatetime` for `datetime.time`
    '''

    format = '%H:%M'

    def from_python(self, value):
        if value is None:
            return ''
        # we don't care about year in time converter, so use native strftime
        return value.strftime(self.format)

    def convert_datetime(self, value):
        return datetime.strptime(value, self.format).time()


class DisplayOnly(Converter):
    """
    Does nothing, always returns a value of field before validation
    """

    def from_python(self, value):
        return value

    def to_python(self, value):
        return self._existing_value


class SplitDateTime(Converter):
    '''
    Converter for FieldSet, allowing get a single `datetime.datetime`
    object from two fields: date and time.
    '''

    def from_python(self, value):
        if value is None:
            return {'date': None, 'time': None}
        else:
            return {'date': value.date(), 'time': value.time()}

    def to_python(self, value):
        if value['date'] is None or value['time'] is None:
            return None
        res = datetime.combine(value['date'], value['time'])
        return res


class Html(Char):
    '''
    Converter for flexible cleanup of HTML document fragments.
    A subclass of :class:`Char<iktomi.forms.convs.Char>`.

    Uses :class:`utils.html.Sanitizer<iktomi.utils.html.Sanitizer>`
    instance to sanitize input HTML.

    Construtor collects from given kwargs all of
    :class:`Sanitizer<iktomi.utils.html.Sanitizer>`
    options and passes them into Sanitizer's constructor.

    For list properties there is :meth:`add_*` interface::

        Html(add_allowed_elements=['span'], add_dom_callbacks=[myfunc])
    '''

    #: A list of allowed HTML elements
    allowed_elements = frozenset(('a', 'p', 'br', 'li', 'ul', 'ol', 'hr', 'u',
                                  'i', 'b', 'blockquote', 'sub', 'sup'))
    #: A list of allowed HTML attributes
    allowed_attributes = frozenset(('href', 'src', 'alt', 'title', 'class',
                                    'rel'))
    #: A list of tags to be dropped if they are empty
    drop_empty_tags = frozenset(('p', 'a', 'u', 'i', 'b', 'sub', 'sup'))
    allowed_protocols = frozenset(['ftp', 'http', 'https', 'mailto',
                                   'tel', 'webcal', 'callto'])
    #: A dict containing an element name as a key and class test as value.
    #: Test can be a set of strings (for simple strict match) or callable
    #: accepting class name and returning True/False.
    #: Set to `None` to allow all classes.
    allowed_classes = {}
    #: A list of callbacks applied to DOM tree before it is
    #: rendered back to HTML.
    dom_callbacks = []
    wrap_inline_tags = None
    split_paragraphs_by_br = True
    # Tags to wrap in paragraphs on top
    tags_to_wrap = ['b', 'big', 'i', 'small', 'tt',
                    'abbr', 'acronym', 'cite', 'code',
                    'dfn', 'em', 'kbd', 'strong', 'samp',
                    'var', 'a', 'bdo', 'br', 'map', 'object',
                    'q', 'span', 'sub', 'sup']
    #: Function returning object marked safe for template engine.
    #: For example, `jinja2.Markup` object.
    Markup = lambda s, x: x
    #: A Cleaner class. Be default, 'iktomi.utils.html.Cleaner' is used.
    #: It is a `lxml.html.clean.Cleaner` subclass
    Cleaner = Cleaner
    class Nothing: pass

    PROPERTIES = ['allowed_elements', 'allowed_attributes', 'allowed_protocols',
                  'allowed_classes', 'dom_callbacks', 'drop_empty_tags',
                  'wrap_inline_tags', 'split_paragraphs_by_br']

    LIST_PROPERTIES = ['allowed_elements', 'allowed_attributes',
                       'allowed_protocols', 'dom_callbacks',
                       'drop_empty_tags', 'tags_to_wrap']

    @classmethod
    def _load_arg(cls, opt):
        assert hasattr(cls, opt)
        # XXX very complicated merges for rare cases
        #     not sure if they are necessary
        if opt in cls.__dict__:
            result = getattr(cls, opt)
        else:
            for base in cls.__bases__:
                if hasattr(base, '_load_arg'):
                    result = base._load_arg(opt)
                    if not result is cls.Nothing:
                        break
            else:
                result = cls.Nothing

        if 'add_' + opt in cls.__dict__:
            add = getattr(cls, 'add_' + opt)
            if result is cls.Nothing:
                result = add
            else:
                result = set(result)
                result.update(add)
        return result

    def __init__(self, *args, **kwargs):
        assert self.Cleaner is not None, \
                'Install lxml or implement your own html cleaner'
        for opt in self.PROPERTIES:
            if not opt in kwargs:
               result = self._load_arg(opt)
               if not result is self.Nothing:
                   kwargs[opt] = result

        for opt in self.LIST_PROPERTIES:
            add_key = 'add_' + opt
            if add_key in kwargs:
                opt_value = kwargs.get(opt, [])
                # XXX sometimes set must be ordered
                kwargs[opt] = set(opt_value)
                kwargs[opt].update(kwargs.pop(add_key))
        Char.__init__(self, *args, **kwargs)

    def clean_value(self, value):
        value = Char.clean_value(self, value)
        try:
            doc = html.fragment_fromstring(value, create_parent=True)
        except XMLSyntaxError: # pragma: no cover. XXX: seems like this exception is
                               # unreachable with create_parent=True,
                               # maybe it should be removed?
            raise ValidationError(N_(u'Error parsing HTML'))
        self.cleaner(doc)
        clean = html.tostring(doc, encoding='utf-8').decode('utf-8')
        clean = clean.split('>', 1)[1].rsplit('<', 1)[0]
        return self.Markup(clean)

    @cached_property
    def cleaner(self):
        return self.Cleaner(allow_tags=self.allowed_elements,
                            safe_attrs=self.allowed_attributes,
                            allow_classes=self.allowed_classes,
                            allowed_protocols=self.allowed_protocols,
                            drop_empty_tags=self.drop_empty_tags,
                            dom_callbacks=self.dom_callbacks,
                            wrap_inline_tags=self.wrap_inline_tags,
                            split_paragraphs_by_br=self.split_paragraphs_by_br,
                            tags_to_wrap=self.tags_to_wrap,
                            )


class List(Converter):
    '''
    Converter for FieldList'''

    _obsolete = Converter._obsolete | set(['filter'])

    def from_python(self, value):
        if value is None:
            value = []
        result = OrderedDict()
        for index, item in enumerate(value):
            result[str(index+1)] = item
        return result

    def to_python(self, value):
        return list(value.values())


class ListOf(Converter):
    '''
    Converter for scalar Fields, applies nested converter to each value
    of the field (i.e. for each value from MultiDict) and returns a list of
    resulting values.

    Usage::

        ListOf(Converter(), *validators, **kwargs)
    '''

    multiple = True

    def __init__(self, *args, **kwargs):
        if args and (isinstance(args[0], Converter) or \
                     (isinstance(args[0], type) and \
                      issubclass(args[0], Converter))):
            conv = args[0]
            args = args[1:]
        else:
            conv = kwargs['conv']
        if 'field' in kwargs:
            conv = conv(field=kwargs['field'])
        kwargs['conv'] = conv
        Converter.__init__(self, *args, **kwargs)

    def to_python(self, value):
        result = []
        for val in value or []:
            val = self.conv.accept(val)
            if val is not None:
                # XXX is it right to ignore None?
                result.append(val)
        return result

    def from_python(self, value):
        return [self.conv.from_python(item) for item in value or []]


class FieldBlockConv(Converter):

    @property
    def _existing_value(self):
        if self.field is not None:
            return self.field.python_data
        return {} # XXX


class SimpleFile(Converter):
    '''
    Simpliest converter for files. Returns a file from webob Request.POST
    "as is".
    '''

    def _is_empty(self, file):
        return file == u'' or file is None #XXX WEBOB ONLY !!!

    def to_python(self, file):
        if not self._is_empty(file):
            return file

    def from_python(self, value):
        return None


class Email(Char):

    regex = re.compile(
        # dot-atom
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
        # Although quoted variant is allowed by spec it's actually not used
        # except by geeks that are looking for problems. But the characters
        # allowed in quoted string are not safe for HTML and XML, so quoted
        # e-mail can't be expressed in such formats directly which is quite
        # common. We prefer to forbid such valid but unsafe e-mails to avoid
        # security problems. To allow quoted names disable non-text characters
        # replacement and uncomment the following lines of regexp:
        ## quoted-string
        #r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|'
        #    r'\\[\001-011\013\014\016-\177])*"'
        r')@(?:[A-Z0-9-]+\.)+[A-Z]{2,6}$', re.IGNORECASE)
    error_regex = N_('incorrect e-mail address')


class ModelDictConv(Converter):
    '''Converts a dictionary to object of `model` class with the same fields.
    It is designed for use in FieldSet'''

    model = None

    def from_python(self, value):
        if value is None:
            # Field set can be optional
            return {}
        result = {}
        field_names = sum([x.field_names for x in self.field.fields], [])
        for field_name in field_names:
            attr = getattr(value, field_name)
            if issubclass(attr.__class__, _AssociationCollection):
                attr = attr.copy()
            result[field_name] = attr
        return result

    def to_python(self, value):
        obj = self.model()
        field_names = sum([x.field_names for x in self.field.fields], [])
        for field_name in field_names:
            field = self.field.get_field(field_name)
            if field.writable:
                setattr(obj, field_name, value[field_name])
        return obj

    @property
    def _existing_value(self):
        if self.field is not None:
            pd = self.field.parent.python_data
            if self.field.name in pd:
                return pd[self.field.name]
            # Return blank self.model instance as initial/default value 
            # if one does not exist
            return self.model()
        return None


class OptionLabel(six.text_type):

    published = False


class ModelChoice(EnumChoice):

    condition = None
    conv = Int(required=False)
    title_field = 'title'

    def __init__(self, *args, **kwargs):
        EnumChoice.__init__(self, *args, **kwargs)
        self.conv = self.conv(field=self.field)

    @property
    def query(self):
        query = self.env.db.query(self.model)
        if isinstance(self.condition, dict):
            query = query.filter_by(**self.condition)
        elif self.condition is not None:
            query = query.filter(self.condition)
        return query

    def from_python(self, value):
        if value is not None:
            return self.conv.from_python(value.id)
        else:
            return ''

    def to_python(self, value):
        try:
            value = self.conv.to_python(value)
        except ValidationError:
            return None
        else:
            if value is not None:
                return self.query.filter_by(id=value).first()

    def get_object_label(self, obj):
        label = OptionLabel(getattr(obj, self.title_field))
        try:
            label.published = obj.publish
        except AttributeError:
            pass
        return label

    def options(self):
        for obj in self.query.all():
            yield self.conv.from_python(obj.id), self.get_object_label(obj)




# Expose all variables defined after imports
__all__ = [x for x
           in set(vars()) - _all2
           if not x.startswith('_')]
del _all2

