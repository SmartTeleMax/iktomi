import six
from sqlalchemy.types import TypeDecorator, String, Text


class StringList(TypeDecorator):

    impl = String

    def process_bind_param(self, value, dialect):
        if value is not None:
            return ','.join(value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return [x for x in value.split(',') if x]


class IntegerList(TypeDecorator):

    impl = String

    def process_bind_param(self, value, dialect):
        if value is not None:
            return ','.join(str(item) for item in value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return [int(item) for item in value.split(',') if item]


try:
    from jinja2 import Markup
except ImportError: # pragma: no cover
    Markup = None


class HtmlBase(TypeDecorator):
    '''Base class for HTML markup types (safe to render in template)'''

    markup_class = Markup

    def process_result_value(self, value, dialect):
        if value is not None:
            return self.markup_class(value)

    def process_bind_param(self, value, dialect):
        if value is not None:
            return six.text_type(value)


class Html(HtmlBase):
    '''
    Factory class for HTML type. Usage:
        Column(Html(Text))
        Column(Html(String(1000)))
        Column(Html(BigText, markup_class=SomeWrapperClass))
    '''

    def __init__(self, _impl, markup_class=None):
        # Callable is useful to be able to pass type classes as well as
        # type objects, for example Html(String) and Html(String(100))
        if callable(_impl):
            _impl = _impl()
        self.impl = _impl
        self.markup_class = markup_class or self.markup_class
        # Don't call base class' __init__ since we reimplemented it in a
        # different way.


# Compatibility classes. Deprecate them?

class HtmlString(HtmlBase):
    impl = String

class HtmlText(HtmlBase):
    impl = Text
