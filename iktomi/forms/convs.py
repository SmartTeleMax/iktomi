# -*- coding: utf-8 -*-
'''
Module containing some predefined form converters - objects designed to
convert and validate form field's data.
'''

import re
from ..utils import weakproxy, replace_nontext
from datetime import datetime
from ..utils.odict import OrderedDict
from ..utils.dt import strftime
from ..utils.deprecation import deprecated
from ..utils import N_, M_, cached_property


class ValidationError(Exception):

    def __init__(self, message=None, by_field=None):
        self.message = message
        self.by_field = by_field or {}

    def fill_errors(self, field):
        form = field.form
        if self.message is not None:
            form.errors[field.input_name] = self.message
        for name, message in self.by_field.items():
            if name.startswith('.'):
                nm, f = name.lstrip('.'), field
                for i in xrange(len(name) - len(nm) - 1):
                    f = f.parent
                name = f.get_field(nm).input_name
            form.errors[name] = message

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__,
                               self.message,
                               self.by_field)


class Converter(object):
    '''
    Base converter with chaining support
    extend this class in order to get custom
    converter.

    Converting:

    :meth:`to_python` method takes value from form
    and converts it to python type.

    :meth:`from_python` method takes value as python
    object and converts it to string or something
    else widget can display.

    Filters and validators:

    Filters are functions performing additional validation and convertation 
    after :meth:`to_python` method. The interface of filters is following::

        def filter_value(conv, value):
            if wrong(value):
                raise ValidationError(..)
            new_value = do_smth(value)
            return new_value

        convs.Char(max_length=2)|convs.Int()

    Validators are shortcuts to filters that do no convertations, but  only
    do assertions. 

        @validator(error_message)
        def validate(conv, value):
            return is_valid(value)

    Both filters and validators can be passed to converter as positional 
    arguments and will be applied after :meth:`to_python` method and 
    `required` check in order they are mentioned.

    Error messages redefinition:

    Set error_<type> parameter to your own message template, for example::

        convs.Char(regex_readable="YY.MM.DD",
                   error_regex='Should match %(regex_readable)s')`
    '''

    # obsolete parameters from previous versions
    _obsolete = frozenset(['max_length', 'min_length', 'null', 'min', 'max',
                           'multiple'])
    required = False
    multiple = False

    #: Values are not accepted by Required validator
    error_required = N_('required field')

    def __init__(self, *args, **kwargs):
        if self._obsolete & set(kwargs):
            raise TypeError(
                    'Obsolete parameters are used: %s' %
                        list(self._obsolete & set(kwargs)))
        self.field = weakproxy(kwargs.get('field'))
        self._init_kwargs = kwargs
        self.__dict__.update(kwargs)
        self.validators_and_filters = args

    @property
    def env(self):
        return self.field.env

    def _is_empty(self, value):
        return value in ('', [], {}, None)

    def accept(self, value, silent=False):
        '''
        Accepts a value from the form, calls :meth:`to_python` method,
        checks `required` condition, applies filters and validators,
        catches ValidationError.

        If `silent=False`, writes errors to `form.errors`.
        '''
        try:
            value = self.to_python(value)
            for v in self.validators_and_filters:
                value = v(self, value)

            if self.required and self._is_empty(value):
                raise ValidationError(self.error_required)
        except ValidationError, e:
            if not silent:
                e.fill_errors(self.field)
            #NOTE: by default value for field is in python_data,
            #      but this is not true for FieldList where data
            #      is dynamic, so we set value to None for absent value.
            value = self._existing_value
        return value

    def to_python(self, value):
        """ custom converters should override this """
        if value == '':
            return None
        return value

    def from_python(self, value):
        """ custom converters should override this """
        if value is None:
            value = ''
        return value

    def __call__(self, *args, **kwargs):
        kwargs = dict(self._init_kwargs, **kwargs)
        kwargs.setdefault('field', self.field)
        validators = tuple(self.validators_and_filters) + args
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

def length(min_length, max_length):
    'Sting length constraint'
    if min_length == max_length:
        message = N_(u'length of value is limited to %(max)d')
    else:
        message = N_('length should be between %(min)d and %(max)d symbols')

    message = message % dict(min=min_length, max=max_length)

    @validator(message)
    def wrapper(conv, value):
        if not value:
            # it meens that this value is not required
            return True
        if len(value) < min_length:
            return False
        if len(value) > max_length:
            return False
        return True
    return wrapper


@deprecated('Use length(min, max) instead.')
def limit(min_length, max_length):
    return length(min_length, max_length)


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
    return between(min_value, max_value)


class CharBased(Converter):

    nontext_replacement = u'\uFFFD' # Set None to disable and empty string to
                                    # remove.
                                    # Default value is u"�"
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

    #: Regexp to match input string
    regex = None

    error_regex = N_('field should match %(regex)s')

    def to_python(self, value):
        # converting
        value = self.clean_value(value)
        if value and self.regex:
            regex = self.regex
            if isinstance(self.regex, basestring):
                regex = re.compile(self.regex, re.U)
            if not regex.match(value):
                error = self.error_regex % {'regex': self.regex}
                raise ValidationError(error)
        return value

    def from_python(self, value):
        if value is None:
            return ''
        return unicode(value)


class Int(Converter):
    """
    integer converter with max and min values support
    """

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
        return unicode(value)


class Bool(Converter):

    required = False

    def to_python(self, value):
        return bool(value)

    def from_python(self, value):
        if value:
            return 'checked'
        return ''


class DisplayOnly(Converter):

    def from_python(self, value):
        return value

    def to_python(self, value):
        return self._existing_value


class EnumChoice(Converter):
    '''In addition to Converter interface it must provide methods options and
    get_label.'''

    conv = Char()
    # choices: [(python_value, label), ...]
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
        conv = self.conv
        for python_value, label in self.choices:
            yield conv.from_python(python_value), label

    def get_label(self, value):
        value = self.conv.accept(value, silent=True)
        return dict(self.choices).get(value)


class BaseDatetime(CharBased):

    format = None
    readable_format = None
    replacements = (('%H', 'HH'), ('%M', 'MM'), ('%d', 'DD'),
                    ('%m', 'MM'), ('%Y', 'YYYY'))
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
            raise ValidationError(self.error_wrong_format)


class Datetime(BaseDatetime):

    format = '%d.%m.%Y, %H:%M'

    def convert_datetime(self, value):
        return datetime.strptime(value, self.format)


class Date(BaseDatetime):

    format = '%d.%m.%Y'

    def convert_datetime(self, value):
        return datetime.strptime(value, self.format).date()


class Time(BaseDatetime):

    format = '%H:%M'

    def from_python(self, value):
        if value is None:
            return ''
        # we don't care about year in time converter, so use native strftime
        return value.strftime(self.format)

    def convert_datetime(self, value):
        return datetime.strptime(value, self.format).time()


class SplitDateTime(Converter):

    def from_python(self, value):
        return {'date':value, 'time':value}

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

    For list properties it is allowed to use :meth:`add_%s` interface::

        Html(add_allowed_elements=['span'], add_dom_callbacks=[myfunc])
    '''

    allowed_elements = frozenset(('a', 'p', 'br', 'li', 'ul', 'ol', 'hr', 'u',
                                  'i', 'b', 'blockquote', 'sub', 'sup'))
    allowed_attributes = frozenset(('href', 'src', 'alt', 'title', 'class', 'rel'))
    drop_empty_tags = frozenset(('p', 'a', 'u', 'i', 'b', 'sub', 'sup'))
    allowed_classes = {}
    #: Function returning object marked safe for template engine.
    #: For example: jinja Markup object
    Markup = lambda s, x: x
    class Nothing: pass

    @classmethod
    def _load_arg(cls, opt):
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
        from ..utils.html import PROPERTIES, LIST_PROPERTIES

        for opt in PROPERTIES:
            if not opt in kwargs:
               result = self._load_arg(opt)
               if not result is self.Nothing:
                   kwargs[opt] = result

        for opt in LIST_PROPERTIES:
            add_key = 'add_' + opt
            if add_key in kwargs:
                kwargs[opt] = set(kwargs.get(opt, LIST_PROPERTIES[opt]))
                kwargs[opt].update(kwargs.pop(add_key))

        super(Html, self).__init__(*args, **kwargs)

    def clean_value(self, value):
        # XXX move the import outside (in try..except)
        from ..utils.html import ParseError

        value = super(Html, self).clean_value(value)
        try:
            clean = self.sanitizer.sanitize(value)
        except ParseError:
            raise ValidationError(u'not valid html')
        else:
            return self.Markup(clean)

    @cached_property
    def sanitizer(self):
        from ..utils.html import Sanitizer
        return Sanitizer(**self._init_kwargs)

    # XXX are these properties used?
    @property
    def tags(self):
        return self.allowed_elements
    @property
    def attrs(self):
        return self.allowed_attributes


class List(Converter):

    _obsolete = Converter._obsolete | set(['filter'])

    def from_python(self, value):
        result = OrderedDict()
        for index, item in enumerate(value):
            result[str(index+1)] = item
        return result

    def to_python(self, value):
        return value.values()


class ListOf(Converter):
    '''
    Usage:
        ListOf(Converter(), *validators_and_filters, **kwargs)
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


class SimpleFile(Converter):

    def _is_empty(self, file):
        return file == u'' or file is None #XXX WEBOB ONLY !!!

    def to_python(self, file):
        if not self._is_empty(file):
            return file

    def from_python(self, value):
        return None

