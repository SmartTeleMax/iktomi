from iktomi.forms.convs import *


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
        if obj.id is not None:
            obj = self.env.db.merge(obj)
            # We have to repeat initialization since merge assumes None as
            # uninitialized.
            for field in self.field.fields:
                setattr(obj, field.name, value[field.name])
        return obj
