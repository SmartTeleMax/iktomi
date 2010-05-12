# -*- coding: utf-8 -*-
'''
Module containing some predefined form converters - objects designed to
convart and validate form field's data.
'''

import re
from ..utils import weakproxy, replace_nontext
from datetime import datetime
from ..utils.odict import OrderedDict


class NotSubmitted(Exception): pass


class SkipReadonly(NotSubmitted): pass


class NestedError(NotSubmitted): pass


class ValidationError(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)

    @property
    def message(self):
        return self.args[0]

    def __str__(self):
        # This method is called by logging, we need it to avoid
        # <unprintable ValidationError object> messages.
        return self.message.encode('utf-8')


class Converter(object):
    '''
    Base converter with chaining support
    extend this class in order to get custom
    converter.

    Converting:

    :meth:`to_python` method takes value from form
    and converts it to python type

    :meth:`from_python` method takes value as python
    object and converts it to string or something
    else widget can display

    Chaining:

    Result of first converter is passed as input value
    to second. for example::

        convs.Char(max_length=2)|convs.Int()

    will be a convertor which first validates
    if string's length is 2 or less and after
    that converts it to integer

    Error messages redefinition:

    Set error_<type> parameter to your own message template, for example::

        convs.Char(min_length=5,
                   error_min_length='At least %(min_length)s characters required')`
    '''

    #: If null is True Converter represents empty value ('' or None) as None
    null = False

    # It is defined as read-only property to avoid setting it to True where
    # converter doesn't support it.
    @property
    def multiple(self):
        '''
        Signs if converter is multiple or not.
        Multiple converters usually accept and return lists.
        '''
        return False

    def __init__(self, field=None, **kwargs):
        self.field = weakproxy(field)
        self._init_kwargs = kwargs
        self.__dict__.update(kwargs)

    @property
    def env(self):
        return self.field.env

    def to_python_wrapper(self, value):
        if self.null and value in ('', None):
            return None
        return self.to_python(value)

    def to_python(self, value):
        """ custom converters should override this """
        return value

    def from_python(self, value):
        """ custom converters should override this """
        return value

    def __or__(self, next):
        """ chaining converters """
        chain = Chain((self, next))
        return chain

    def __call__(self, **kwargs):
        kwargs = dict(self._init_kwargs, **kwargs)
        kwargs.setdefault('field', self.field)
        return self.__class__(**kwargs)

    def _assert(self, expression, message_template, error_type=None):
        if not expression:
            if error_type is not None:
                message_template = getattr(self, 'error_'+error_type,
                                           message_template)
            message = message_template % self.__dict__
            raise ValidationError(message)


class Chain(Converter):
    """
    wrapper for chained converters
    """

    def __init__(self, convs=(), field=None, **kwargs):
        self.field = weakproxy(field)
        if field:
            convs = (conv(field=field) for conv in convs)
        self.convs = tuple(convs)
        super(Chain, self).__init__(**kwargs)

    def to_python(self, value):
        for conv in self.convs:
            value = conv.to_python_wrapper(value)
        return value

    def from_python(self, value):
        for conv in reversed(self.convs):
            value = conv.from_python(value)
        return value

    def __or__(self, next):
        return Chain(self.convs+(next,))

    def __ior__(self, next):
        self.convs += (next,)
        return self

    def __call__(self, convs=None, **kwargs):
        if convs is None:
            convs = self.convs
        return Converter.__call__(self, convs=convs, **kwargs)


from pytils.numeral import get_plural

def plural_chars(n):
    return get_plural(n, [u'символа', u'cимволов', u'символов'])

def plural_char(n):
    return get_plural(n, [u'символ', u'символа', u'символов'])


class Char(Converter):

    """
    string converter with min length, max length and regex
    checks support
    """

    #: Min length of valid string
    min_length = None
    #: Max length of valid string
    max_length = None
    #: Regexp to match input string
    regex = None
    #: Option showing whether strip input string or not. True by default
    strip = True
    nontext_replacement = u'\uFFFD' # Set None to disable and empty string to
                                    # remove.

    def clean_value(self, value):
        '''
        Additional clean action to preprocess value before :meth:`to_python`
        method.

        Subclasses may define own clean_value method to allow additional clean
        actions like html cleanup, etc.
        '''
        # We have to clean before checking min/max length. It's done in
        # separate method to allow additional clean action in subclasses.
        if value is None:
            value = ''
        if self.strip:
            value = value.strip()
        return value

    def to_python(self, value):
        value = self.clean_value(value)
        if self.nontext_replacement is not None:
            value = replace_nontext(value, self.nontext_replacement)
        if self.max_length==self.min_length!=None:
            self._assert(len(value) == self.max_length,
                         u'Длина должна быть ровно ' + plural_char(self.max_length), 'min_length')
        else:
            if self.max_length:
                self._assert(len(value) <= self.max_length,
                             u'Длина должна быть не более ' + plural_chars(self.max_length), 'max_length')
            if self.min_length:
                if self.min_length == 1:
                    self._assert(len(value) >= self.min_length,
                                 u'Поле не должно быть пустым', 'min_length')
                else:
                    self._assert(len(value) >= self.min_length,
                                 u'Длина должна быть не менее ' + plural_chars(self.min_length), 'min_length')
        if self.regex:
            regex = self.regex
            if isinstance(self.regex, basestring):
                regex = re.compile(self.regex, re.U)
            self._assert(regex.match(value),
                         'field should match %(regex)s', 'regex')
        return value

    def from_python(self, value):
        if value is None:
            return ''
        return unicode(value)


class Int(Converter):
    """
    integer converter with max and min values support
    """

    #: Min allowed valid number
    min = None
    #: Max allowed valid number
    max = None

    def to_python(self, value):
        if value is None:
            if self.null:
                return None
            value = ''
        try:
            value = int(value)
        except ValueError:
            self._assert(False, 'it is not valid integer')
        if self.min is not None:
            self._assert(self.min <= value, 'min value is %(min)s', 'min')
        if self.max is not None:
            self._assert(self.max >= value, 'max value is %(max)s', 'max')
        return value

    def from_python(self, value):
        if value is None:
            return ''
        return unicode(value)

    def __call__(self, **kwargs):
        kwargs.setdefault('min', self.min)
        kwargs.setdefault('max', self.max)
        return Converter.__call__(self, **kwargs)


class Bool(Converter):

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

    conv = Converter()
    # choices: [(python_value, label), ...]
    choices = ()
    multiple = False

    def from_python(self, value):
        if self.multiple:
            return [self.conv.from_python(item) for item in value or []]
        else:
            return self.conv.from_python(value)

    def _safe_to_python(self, value):
        try:
            value = self.conv.to_python(value)
        except ValidationError:
            return None
        if value not in dict(self.choices):
            return None
        return value

    def to_python(self, value):
        if self.multiple:
            value = [item for item in map(self._safe_to_python, value or [])
                     if item is not None]
        else:
            value = self._safe_to_python(value)
        if not self.null:
            self._assert(value not in (None, []),
                         'you must select a value', 'null')
        return value

    def __iter__(self):
        for python_value, label in self.choices:
            yield self.conv.from_python(python_value), label

    def get_label(self, value):
        return dict(self.choices).get(self.conv.to_python(value))


class DatetimeDisplay(DisplayOnly):

    format = '%d.%m.%Y, %H:%M'

    def from_python(self, value):
        if not value:
            return u'не задано'
        return value.strftime(self.format)


class Datetime(Converter):

    format = '%d.%m.%Y, %H:%M'

    def from_python(self, value):
        if not value:
            return ''
        return value.strftime(self.format)

    def to_python(self, value):
        if not value and not self.null:
            raise ValidationError, u'обязательное поле'
        try:
            return datetime.strptime(value, self.format)
        except ValueError:
            # XXX Message is format dependent
            raise ValidationError, u'неверный формат (ДД.ММ.ГГГГ, ЧЧ:ММ)'


class Date(Converter):

    format = '%d.%m.%Y'

    def from_python(self, value):
        if not value:
            return ''
        return value.strftime(self.format)

    def to_python(self, value):
        if not value and not self.null:
            raise ValidationError, u'обязательное поле'
        elif not value:
            return None
        try:
            return datetime.strptime(value, self.format).date()
        except ValueError:
            # XXX Message is format dependent
            raise ValidationError, u'неверный формат (ДД.ММ.ГГГГ)'


class Time(Converter):

    format = '%H:%M'

    def from_python(self, value):
        if value in (None, ''):
            return ''
        return value.strftime(self.format)

    def to_python(self, value):
        if not value and not self.null:
            raise ValidationError, u'обязательное поле'
        try:
            return datetime.strptime(value, self.format).time()
        except ValueError:
            # XXX Message is format dependent
            raise ValidationError, u'неверный формат (ЧЧ:ММ)'


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
    '''
    Converter for flexible cleanup of HTML document fragments.
    A subclass of :class:`Char<insanities.forms.convs.Char>`.

    Uses :class:`utils.html.Sanitizer<insanities.utils.html.Sanitizer>`
    instance to sanitize input HTML.

    Construtor collects from given kwargs all of
    :class:`Sanitizer<insanities.utils.html.Sanitizer>`
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
    Markup = lambda x: x

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
            raise ValidationError, u'not valid html'
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
    min_length = None
    max_length = None

    def from_python(self, value):
        result = OrderedDict()
        for index, item in enumerate(value):
            result[str(index+1)] = item
        return result

    def to_python(self, value):
        items = value.values()
        if self.filter is not None:
            items = filter(self.filter, items)
        if self.max_length:
            self._assert(len(items)<=self.max_length,
                         'max length is %(max_length)s', 'max_length')
        if self.min_length:
            self._assert(len(value)>=self.min_length,
                         'min length is %(min_length)s', 'min_length')
        return items
