import re
from iktomi.forms.convs import *
from iktomi.utils import N_


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
        result = {}
        for field in self.field.fields:
            result[field.name] = getattr(value, field.name)
        return result

    def to_python(self, value):
        obj = self.model()
        for field in self.field.fields:
            setattr(obj, field.name, value[field.name])
        return obj
