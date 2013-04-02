# -*- coding: utf-8 -*-
import unittest
from copy import copy

from iktomi.forms import *
from webob.multidict import MultiDict


class FieldTests(unittest.TestCase):

    def test_accept(self):
        'Method accept of bound field returns cleaned value'
        class _Form(Form):
            fields=[Field('input', convs.Char())]
        form = _Form()
        self.assert_(form.accept(MultiDict(input='value')))
        self.assertEqual(form.python_data['input'], 'value')

    def test_get_field(self):
        class F(Form):
            fields = [
                FieldSet('fieldset', fields=[
                    FieldList('fieldlist',
                        field=FieldSet(None, fields=[
                            Field('subfield')
                        ])
                    )
                ])
            ]

        form = F()
        for nm, cls in [('fieldset', FieldSet),
                        ('fieldset.fieldlist', FieldList),
                        ('fieldset.fieldlist-1', FieldSet),
                        ('fieldset.fieldlist-1.subfield', Field),
                        ]:
            self.assert_(isinstance(form.get_field(nm), cls),
                         '%s is not instance of %s' % (nm, cls))
            self.assertEqual(form.get_field(nm).input_name, nm)
