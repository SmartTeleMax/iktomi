
from sqlalchemy.databases.mysql import MSMediumText as MediumText
from sqlalchemy import String, Integer, Text, Boolean, Date, DateTime
from sqlalchemy import orm, types, create_engine


class StringList(types.TypeDecorator):

    impl = types.String

    def process_bind_param(self, value, dialect):
        if value is not None:
            return ','.join(value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return filter(None, value.split(','))


class IntegerList(types.TypeDecorator):

    impl = types.String

    def process_bind_param(self, value, dialect):
        if value is not None:
            return ','.join(str(item) for item in value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return [int(item) for item in value.split(',') if item]


def get_html_class(safe_marker, impl_=types.Text):
    
    class HtmlTextJinja(types.TypeDecorator):
        '''Represants safe to render in template html markup'''
        
        impl = impl_
        
        def process_result_value(self, value, dialect):
            if value is not None:
                return safe_marker(value)
        
        def process_bind_param(self, value, dialect):
            if value is not None:
                return unicode(value)

    return HtmlTextJinja

try:
    from jinja2 import Markup
except ImportError:
    pass
else:
    HtmlTextJinja = get_html_class(Markup)
    HtmlStringJinja = get_html_class(Markup, impl=types.String)
    HtmlMediumTextJinja = get_html_class(Markup, impl=types.MediumText)
