# -*- coding: utf-8 -*-
'''
Module containing some predefined form converters - objects designed to
convert and validate form field's data.
'''

import re
from datetime import datetime
from ..utils import weakproxy, replace_nontext, N_
from ..utils.dt import strftime
from ..utils.odict import OrderedDict


class NotSubmitted(Exception): pass


class SkipReadonly(NotSubmitted): pass


class NestedError(NotSubmitted): pass


class ValidationError(Exception):

    @property
    def message(self):
        return self.args[0]

    def __repr__(self):
        return self.messages.encode('utf-8')


class Converter(object):

    required = True
    errors = {}
    default_errors = {
        'required': N_(u'required field'),
        'incorrect': N_(u'incorrect value'),
    }

    def __init__(self, *args, **kwargs):
        self.field = weakproxy(kwargs.get('field'))
        self._init_kwargs = kwargs
        self.__dict__.update(kwargs)
        self.validators_and_filters = args
        self.to_python = self._check(self.to_python)

    class AttributeLookup:
        def __init__(self, *namespaces):
            self.namespaces = namespaces
        def __getattr__(self, name):
            for namespace in self.namespaces:
                if name in namespace:
                    return namespace[name]
            raise AttributeError(name)

    @property
    def error_templates(self):
        env_errors = {}
        if 'error_templates' in self.env:
            env_errors = self.env.error_templates
        return self.AttributeLookup(self.errors, env_errors, self.default_errors)

    def raise_error(self, message_template, **kw):
        raise ValidationError(self.env.format_error(message_template, **kw))

    @property
    def multiple(self):
        '''
        Signs if converter is multiple or not.
        Multiple converters usually accept and return collections.
        '''
        return False

    @property
    def env(self):
        return self.field.env

    def is_empty(self, value):
        return value in ('', [], {})

    def _check(self, method):
        def wrapper(value, **kwargs):
            field, form = self.field, self.field.form
            if self.required and self.is_empty(value):
                form.errors[self.field.input_name] = self.env.format_error(self.error_templates.required)
                return self.field.parent.python_data[field.name]
            try:
                value = method(value, **kwargs)
                for v in self.validators_and_filters:
                    value = v(value)
            except ValidationError, e:
                form.errors[field.input_name] = e.message
                #NOTE: by default value for field is in python_data,
                #      but this is not true for FieldList where data
                #      is dynamic, so we set value to None for absent value.
                value = field.parent.python_data.get(field.name)
            return value
        return wrapper

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

    def __call__(self, **kwargs):
        kwargs = dict(self._init_kwargs, **kwargs)
        kwargs.setdefault('field', self.field)
        return self.__class__(*self.validators_and_filters, **kwargs)


class validator(object):
    'Function decorator'
    def __init__(self, message):
        self.message = message
    def __call__(self, func):
        def wrapper(value):
            if not func(value):
                raise ValidationError(self.message)
            return value
        return wrapper

# Some useful validators

def limit(min_length, max_length):
    'Sting length constraint'
    message = 'length should be between %(min)d and %(max)d symbols' % dict(min=min_length, max=max_length)

    @validator(message)
    def wrapper(value):
        if not value:
            # it meens that this value is not required
            return True
        if len(value) < min_length:
            return False
        if len(value) > max_length:
            return False
        return True
    return wrapper


def num_limit(min_value, max_value):
    'Numerical values limit'
    message = 'value should be between %(min)d and %(max)d' % dict(min=min_value, max=max_value)

    @validator(message)
    def wrapper(value):
        if not value:
            # it meens that this value is not required
            return True
        if value < min_value:
            return False
        if value > max_value:
            return False
        return True
    return wrapper


def length(*args):
    'Exact string lengths'
    @validator(u'Length of value is limited to ' + ','.join([str(a) for a in args]))
    def wrapper(value):
        if not value:
            return True
        if not len(str(value)) in args:
            return False
        return True
    return wrapper


@validator(u'Value must be positive')
def positive_num(value):
    if not value:
        return True
    return value > 0


class Char(Converter):

    #: Regexp to match input string
    regex = None
    nontext_replacement = u'\uFFFD' # Set None to disable and empty string to
                                    # remove.
    strip=False

    errors = {'regex': N_(u'field should match %(regex)s')}

    def clean_value(self, value):
        '''
        Additional clean action to preprocess value before :meth:`to_python`
        method.

        Subclasses may define own clean_value method to allow additional clean
        actions like html cleanup, etc.
        '''
        # We have to clean before checking min/max length. It's done in
        # separate method to allow additional clean action in subclasses.
        if self.strip:
            value = value.strip()
        return value

    def to_python(self, value):
        # converting
        value = self.clean_value(value)
        if self.regex:
            regex = self.regex
            if isinstance(self.regex, basestring):
                regex = re.compile(self.regex, re.U)
            if not regex.match(value):
                self.raise_error(self.error_templates.regex, regex=self.regex)
        return value

    def from_python(self, value):
        if value is None:
            return ''
        return unicode(value)


class Int(Converter):
    """
    integer converter with max and min values support
    """

    errors = {'incorrect': N_(u'it is not valid integer')}

    def to_python(self, value):
        if value == '':
            return None
        try:
            value = int(value)
        except ValueError:
            self.raise_error(self.error_templates.incorrect)
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
        raise SkipReadonly


class EnumChoice(Converter):
    '''In addition to Converter interface it must provide methods __iter__ and
    get_label.'''

    conv = Char()
    # choices: [(python_value, label), ...]
    choices = ()
    multiple = False
    errors = {'required': N_(u'you must select a value')}

    def from_python(self, value):
        conv = self.conv(field=self.field)
        if self.multiple:
            return [conv.from_python(item) for item in value or []]
        else:
            return conv.from_python(value)

    def _safe_to_python(self, value):
        conv = self.conv(field=self.field)
        try:
            value = conv.to_python(value)
        except ValidationError:
            return None
        if value not in dict(self.choices):
            return None
        return value

    def to_python(self, value):
        if value == '':
            #XXX: check for multiple?
            if self.multiple:
                return []
            return None
        if self.multiple:
            value = [item for item in map(self._safe_to_python, value or [])
                     if item is not None]
        else:
            value = self._safe_to_python(value)
        return value

    def __iter__(self):
        conv = self.conv(field=self.field)
        for python_value, label in self.choices:
            yield conv.from_python(python_value), label

    def get_label(self, value):
        conv = self.conv(field=self.field)
        return dict(self.choices).get(conv.to_python(value))


class BaseDatetime(Converter):

    format = None
    readable_format = None
    replacements = (('%H', 'HH'), ('%M', 'MM'), ('%d', 'DD'),
                    ('%m', 'MM'), ('%Y', 'YYYY'))
    errors = {'wrong_format': N_(u'wrong format (%(readable_format)s)')}

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
        if not value:
            return None
        try:
            return self.convert_datetime(value)
        except ValueError:
            self.raise_error(self.error_templates.wrong_format, readable_format=self.readable_format)
        except TypeError, e:
            self.raise_error(unicode(e))


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
        if value['date'] is None:
            return None
        res = datetime.combine(value['date'], value['time'])
        return res


class Joiner(object):

    def join(self, values):
        return values

    def split(self, value):
        return value

    def __call__(self):
        return self.__class__()


class DatetimeJoiner(Joiner):
    # XXX Two classes to split and join datetimes?
    def join(self, values):
        return datetime.combine(*values)

    def split(self, value):
        if not value:
            return None, None
        return value.date(), value.time()


class Html(Char):
    allowed_elements = frozenset(('a', 'p', 'br', 'li', 'ul', 'ol', 'hr', 'u',
                                  'i', 'b', 'blockquote', 'sub', 'sup'))
    allowed_attributes = frozenset(('href', 'src', 'alt', 'title', 'class', 'rel'))
    drop_empty_tags = frozenset(('p', 'a', 'u', 'i', 'b', 'sub', 'sup'))
    allowed_classes = {}
    #: Function returning object marked safe for template engine.
    #: For example: jinja Markup object
    Markup = lambda s, x: x
    errors = {'incorrect': N_(u'not valid html')}

    def _load_arg(self, kwargs, opt):
        if hasattr(self, opt):
            kwargs.setdefault(opt, getattr(self, opt))

    def __init__(self, **kwargs):
        from ..utils.html import PROPERTIES, LIST_PROPERTIES

        for opt in PROPERTIES:
            if not opt in kwargs:
                # passed throught kwargs set is stronger then stored in class
                # add_%  
                self._load_arg(kwargs, 'add_' + opt)
            self._load_arg(kwargs, opt)

        for opt in LIST_PROPERTIES:
            add_key = 'add_' + opt
            if add_key in kwargs:
                kwargs[opt] = set(kwargs.get(opt, LIST_PROPERTIES[opt]))
                kwargs[opt].update(kwargs.pop(add_key))

        super(Html, self).__init__(**kwargs)

    def clean_value(self, value):
        from ..utils.html import ParseError, Sanitizer

        value = super(Html, self).clean_value(value)
        sanitizer = Sanitizer(**self._init_kwargs)
        try:
            clean = sanitizer.sanitize(value)
        except ParseError:
            self.raise_error(self.error_templates.incorrect)
        else:
            return self.Markup(clean)

    @property
    def tags(self):
        return self.allowed_elements
    @property
    def attrs(self):
        return self.allowed_attributes


class List(Converter):

    filter = None

    def from_python(self, value):
        result = OrderedDict()
        for index, item in enumerate(value):
            result[str(index+1)] = item
        return result

    def to_python(self, value):
        items = value.values()
        if self.filter is not None:
            items = filter(self.filter, items)
        return items

class SimpleFile(Converter):

    def is_empty(self, file):
        return file == u'' or file is None #XXX WEBOB ONLY !!!

    def to_python(self, file):
        if not self.is_empty(file):
            return file

    def from_python(self, value):
        return None

