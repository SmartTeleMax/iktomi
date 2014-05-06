# -*- coding: utf-8 -*-
from sqlalchemy.ext.associationproxy import _AssociationCollection
from iktomi.forms.convs import *
from iktomi.forms.convs import __all__ as _all1

import re
from iktomi.utils import N_

_all2 = locals().keys()


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
            if 'w' in field.permissions:
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
        return [] if self.multiple else None


class OptionLabel(unicode):

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

    def get_label(self, form_value):
        obj = self._safe_to_python(form_value)
        if obj is not None:
            return self.get_object_label(obj)

    def options(self):
        for obj in self.query.all():
            yield self.conv.from_python(obj.id), self.get_object_label(obj)


# Expose all variables defined after imports and all variables imported from
# parent module
__all__ = [x for x
           in set(locals().keys()) - (set(_all2) - set(_all1))
           if not x.startswith('_')]
del _all1, _all2
