# -*- coding: utf-8 -*-
__all__ = ['UrlTemplateTests']

import unittest
from iktomi.web.url_templates import UrlTemplate, construct_re
from iktomi.web.url_converters import Converter

class UrlTemplateTests(unittest.TestCase):

    def test_empty_match(self):
        'UrlTemplate match method with empty template'
        ut = UrlTemplate('')
        self.assertEqual(ut.match(''), ('', {}))
        self.assertEqual(ut.match('/'), (None, {}))

    def test_match_without_params(self):
        'UrlTemplate match method without params'
        ut = UrlTemplate('simple')
        self.assertEqual(ut.match('simple'), ('simple', {}))
        self.assertEqual(ut.match('/simple'), (None, {}))

    def test_match_with_params(self):
        'UrlTemplate match method with params'
        ut = UrlTemplate('/simple/<int:id>')
        self.assertEqual(ut.match('/simple/2'), ('/simple/2', {'id':2}))
        self.assertEqual(ut.match('/simple'), (None, {}))
        self.assertEqual(ut.match('/simple/d'), (None, {}))

    def test_match_from_begining_without_params(self):
        'UrlTemplate match method without params (from begining of str)'
        ut = UrlTemplate('simple', match_whole_str=False)
        self.assertEqual(ut.match('simple'), ('simple', {}))
        self.assertEqual(ut.match('simple/sdffds'), ('simple', {}))
        self.assertEqual(ut.match('/simple'), (None, {}))
        self.assertEqual(ut.match('/simple/'), (None, {}))

    def test_match_from_begining_with_params(self):
        'UrlTemplate match method with params (from begining of str)'
        ut = UrlTemplate('/simple/<int:id>', match_whole_str=False)
        self.assertEqual(ut.match('/simple/2'), ('/simple/2', {'id':2}))
        self.assertEqual(ut.match('/simple/2/sdfsf'), ('/simple/2', {'id':2}))
        self.assertEqual(ut.match('/simple'), (None, {}))
        self.assertEqual(ut.match('/simple/d'), (None, {}))
        self.assertEqual(ut.match('/simple/d/sdfsdf'), (None, {}))

    def test_builder_without_params(self):
        'UrlTemplate builder method (without params)'
        ut = UrlTemplate('/simple')
        self.assertEqual(ut(), '/simple')

    def test_builder_with_params(self):
        'UrlTemplate builder method (with params)'
        ut = UrlTemplate('/simple/<int:id>/data')
        self.assertEqual(ut(id=2), '/simple/2/data')

    def test_only_converter_is_present(self):
        ut = UrlTemplate('<int:id>')
        self.assertEqual(ut(id=2), '2')

    def test_default_converter(self):
        ut = UrlTemplate('<message>')
        self.assertEqual(ut(message='hello'), 'hello')

    def test_redefine_converters(self):
        from iktomi.web.url_converters import Integer

        class DoubleInt(Integer):
            def to_python(self, value, env=None):
                return Integer.to_python(self, value, env) * 2
            def to_url(self, value):
                return str(value / 2)

        ut = UrlTemplate('/simple/<int:id>',
                         converters={'int': DoubleInt})
        self.assertEqual(ut(id=2), '/simple/1')
        self.assertEqual(ut.match('/simple/1'), ('/simple/1', {'id': 2}))

    def test_var_name_with_underscore(self):
        ut = UrlTemplate('<message_uid>')
        self.assertEqual(ut(message_uid='uid'), 'uid')

    def test_trailing_delimiter(self):
        self.assertRaises(ValueError, UrlTemplate, '<int:id:>')

    def test_empty_param(self):
        self.assertRaises(ValueError, UrlTemplate, '<>')

    def test_delimiter_only(self):
        self.assertRaises(ValueError, UrlTemplate, '<:>')

    def test_type_and_delimiter(self):
        self.assertRaises(ValueError, UrlTemplate, '<int:>')

    def test_empty_type(self):
        self.assertRaises(ValueError, UrlTemplate, '<:id>')

    def test_no_delimiter(self):
        self.assertRaises(ValueError, UrlTemplate, '<any(x,y)slug>')

    def test_anonymous(self):

        class SimpleConv(Converter):
            regex = '.+'

        convs = {'string': SimpleConv}

        ut = UrlTemplate('/simple/<id>')

        regexp = construct_re(ut.template,
                              converters=convs,
                              anonymous=True)[0]
        self.assertEqual(regexp.pattern, r'^\/simple\/.+')

        regexp = construct_re(ut.template,
                              converters=convs,
                              anonymous=False)[0]
        self.assertEqual(regexp.pattern, r'^\/simple\/(?P<id>.+)')
