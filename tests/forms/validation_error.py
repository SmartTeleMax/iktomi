# -*- coding: utf-8 -*-

import unittest

from iktomi.forms import *
from iktomi.forms.convs import ValidationError


def init_field(name='name'):
    class f(Form):
        fields = [Field(name)]
    return f().get_field(name)

class ValidationErrorTests(unittest.TestCase):

    def test_repr(self):
        r = "%r" % ValidationError(u'Ошибка error', {'.field': u'Ошибка'})
        self.assert_('error' in r)
        self.assert_('.field' in r)

    def test_message(self):
        field = init_field()
        form = field.form

        ve = ValidationError(u'Ошибка')

        ve.fill_errors(field)
        self.assertEqual(form.errors, {'name': u'Ошибка'})

    def test_by_field(self):
        field = init_field()
        form = field.form

        ve = ValidationError(by_field={'.subfield': u'Ошибка-1',
                                       '-2.subfield': u'Ошибка-2',
                                       'field': u'Ошибка-3',
                                       # XXX what does this mean?
                                       '': u'Ошибка-4'}) 

        ve.fill_errors(field)
        self.assertEqual(form.errors, {'name.subfield': u'Ошибка-1',
                                       'name-2.subfield': u'Ошибка-2',
                                       'field': u'Ошибка-3',
                                       '': u'Ошибка-4'})

