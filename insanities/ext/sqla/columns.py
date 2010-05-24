
from sqlalchemy.databases.mysql import MSMediumText as MediumText
from sqlalchemy import String, Integer, Text, Boolean, Date, DateTime
from sqlalchemy import orm, types, create_engine

from ...forms.files import StoredFile, StoredImageFile

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


class AlchemyFile(types.TypeDecorator):

    impl = types.Binary
    file_class = StoredFile # must be subclass of StoredFile

    def __init__(self, base_path=None, base_url=None):
        assert base_path and base_url
        super(AlchemyFile, self).__init__(255)
        self.base_path = base_path
        self.base_url = base_url

    def process_bind_param(self, value, dialect):
        if isinstance(value, StoredFile):
            return value.filename
        return value

    def process_result_value(self, value, dialect):
        if value:
            return self.file_class(value, base_path=self.base_path,
                                   base_url=self.base_url)
        return value

    def copy(self):
        return self.__class__(base_path=self.base_path, base_url=self.base_url)


class AlchemyImageFile(AlchemyFile):

    file_class = StoredImageFile


