# -*- coding: utf-8 -*-

import unittest
from iktomi.forms import *
from iktomi.forms.media import FormJSRef, FormCSSRef, FormMedia
from iktomi.forms.widgets import Widget


class MediaTests(unittest.TestCase):

    def test_form_media_empty(self):
        'Simple form get_media() method'
        class F(Form):
            fields=[Field('name')]
        form = F()
        self.assertEqual(form.get_media(), FormMedia())

    def test_form_media_simple(self):
        'Simple form with multiple fields get_media() method'
        class F(Form):
            fields=[Field('name'),
                    Field('name1')]
        form = F()
        self.assertEqual(form.get_media(), FormMedia())

    def test_form_media_one(self):
        'Custom media in one of field'
        class F(Form):
            fields=[Field('name',
                          widget=Widget(media=FormCSSRef('field.css'))),
                    Field('name1')]
        form = F()
        self.assertEqual(form.get_media(), 
                         FormMedia(FormCSSRef('field.css')))

    def test_form_media_same(self):
        'Same media in both fields'
        class F(Form):
            fields=[Field('name',
                          widget=Widget(media=FormCSSRef('field.css'))),
                    Field('name1',
                          widget=Widget(media=FormCSSRef('field.css')))]
        form = F()
        self.assertEqual(form.get_media(), 
                         FormMedia(FormCSSRef('field.css')))

    def test_form_media_multi(self):
        'Multi media atoms in field'
        class F(Form):
            fields=[Field('name', 
                          widget=Widget(media=[
                              FormCSSRef('field.css'),
                              FormJSRef('field.js')
                          ])),
                    Field('name1', 
                          widget=Widget(media=FormCSSRef('field.css')))]
        form = F()
        self.assertEqual(form.get_media(), 
                         FormMedia(items=[FormCSSRef('field.css'),
                                          FormJSRef('field.js')]))

    def test_fieldset(self):
        'Fieldset media'
        class F(Form):
            fields=[
                FieldSet('set', fields=[
                    Field('name', widget=Widget(media=[
                            FormCSSRef('field.css'),
                            FormJSRef('field.js')])),
                    Field('name1', widget=Widget(media=FormCSSRef('field.css')))
                ], widget=widgets.FieldSetWidget(media=FormCSSRef('fieldset.css')))
            ]
        form = F()
        self.assertEqual(form.get_media(), 
                         FormMedia(items=[FormCSSRef('fieldset.css'),
                                          FormCSSRef('field.css'),
                                          FormJSRef('field.js'),]))

