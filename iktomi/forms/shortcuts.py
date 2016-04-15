# -*- coding: utf-8 -*-

from . import convs, widgets, fields
from iktomi.utils.i18n import N_


class PasswordConv(convs.Char):

    error_mismatch = N_('password and confirm mismatch')
    error_required = N_('password required')

    def from_python(self, value):
        return dict([(field.name, None) for field in self.field.fields])

    def get_initial(self):
        return ''

    def to_python(self, value):
        etalon = value[list(value)[0]]
        for field in self.field.fields:
            self.assert_(value[field.name] == etalon,
                         self.error_mismatch)
        if self.required:
            self.assert_(etalon not in (None, ''), self.error_required)
        elif etalon in (None, ''):
            return None
        return etalon


def PasswordSet(name='password',
                 min_length=3, max_length=200, required=False,
                 password_label=None, confirm_label='confirm', filters=(),
                 **kwargs):
        # class implementation has problem with Fieldset copying:
        # it requires to save all kwargs in object's __dict__
        char = convs.Char(convs.length(min_length, max_length), *filters,
                          **dict(required=required))
        items = (('pass', password_label), ('conf', confirm_label))
        kwargs['fields'] = [fields.Field(subfieldname,
                                         conv=char,
                                         label=label,
                                         widget=widgets.PasswordInput)
                            for subfieldname, label in items]
        kwargs.setdefault('conv', PasswordConv(required=required))
        kwargs.setdefault('widget', widgets.FieldSetWidget(
            template='widgets/fieldset-line'))
        return fields.FieldSet(name, get_initial=lambda: '', **kwargs)

