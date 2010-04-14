
from sqlalchemy.databases.mysql import MSMediumText as MediumText
from sqlalchemy import String, Integer, Text, Boolean, Date, DateTime
from sqlalchemy import orm, types, create_engine

# XXX customize safe_text marker
from jinja2 import Markup

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



class HtmlText(types.TypeDecorator):
    
    impl = types.Text
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return Markup(value)
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return unicode(value)

class HtmlString(HtmlText):
    
    impl = types.String


class HtmlMediumText(HtmlText):
    
    impl = MediumText