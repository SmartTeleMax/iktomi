# -*- coding: utf-8 -*-

import unittest
from iktomi.forms import *


class MediaTests(unittest.TestCase):

    def test_form_media(self):
        'Simple form get_media() method'
        class F(Form):
            fields=[Field('name', convs.Char)]
        form = F()
        self.assertEqual(form.get_media(), media.FormMedia())

    def test_form_media1(self):
        'Simple form with multiple fields get_media() method'
        class F(Form):
            fields=[Field('name', convs.Char),
                    Field('name1', convs.Char)]
        form = F()
        self.assertEqual(form.get_media(), media.FormMedia())

    def test_form_media2(self):
        'Custom media in one of field'
        class F(Form):
            fields=[Field('name', convs.Char, media=media.FormCSSRef('field.css')),
                    Field('name1', convs.Char)]
        form = F()
        self.assertEqual(form.get_media(), 
                         media.FormMedia(media.FormCSSRef('field.css')))

    def test_form_media3(self):
        'Same media in both fields'
        class F(Form):
            fields=[Field('name', convs.Char, media=media.FormCSSRef('field.css')),
                    Field('name1', convs.Char, media=media.FormCSSRef('field.css'))]
        form = F()
        self.assertEqual(form.get_media(), 
                         media.FormMedia(media.FormCSSRef('field.css')))

    def test_form_media4(self):
        'Multi media atoms in field'
        class F(Form):
            fields=[Field('name', convs.Char, media=[
                        media.FormCSSRef('field.css'),
                        media.FormJSRef('field.js')]),
                    Field('name1', convs.Char, media=media.FormCSSRef('field.css'))]
        form = F()
        self.assertEqual(form.get_media(), 
                         media.FormMedia(items=[media.FormCSSRef('field.css'),
                                                media.FormJSRef('field.js')]))

    def test_fieldset(self):
        'Fieldset media'
        class F(Form):
            fields=[
                FieldSet('set', fields=[
                    Field('name', convs.Char, media=[
                            media.FormCSSRef('field.css'),
                            media.FormJSRef('field.js')]),
                    Field('name1', convs.Char, media=media.FormCSSRef('field.css'))])
                ]
        form = F()
        self.assertEqual(form.get_media(), 
                         media.FormMedia(items=[media.FormCSSRef('field.css'),
                                                media.FormJSRef('field.js')]))
