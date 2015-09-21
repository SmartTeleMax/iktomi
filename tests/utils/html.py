# -*- coding: utf-8 -*-
import unittest
import os
import re
from iktomi.utils import html
from lxml.html import Element

class TestSanitizer(unittest.TestCase):
    '''Tests for sanitizer based on lxml'''

    def setUp(self):
        self.attrs = {
            'allow_tags': ['a', 'p', 'br', 'li', 'ul', 'ol', 'hr', 'u', 'i', 'b',
                          'blockquote', 'sub', 'sup', 'span'],
            'safe_attrs': ['href', 'src', 'alt', 'title', 'class', 'rel'],
            'drop_empty_tags': ['p', 'a', 'u', 'i', 'b', 'sub', 'sup'],
            'allow_classes': {},
            'tags_to_wrap': [],
            #'strip_whitespace': True,
        }

    def sanitize(self, text):
        return html.sanitize(text, **self.attrs)

    def assertSanitize(self, text, right):
        res = self.sanitize(text)
        self.assertEqual(res, right)

    def test_safe_attrs(self):
        self.assertSanitize('<p notsafeattr="s" abbr="1" alt="Alt">Safe p</p>',
                            '<p alt="Alt">Safe p</p>')

    def test_safe_tags(self):
        self.assertSanitize('<p alt="Alt">Safe p <script>bad_script()</script></p> <accept>acc</accept>',
                            '<p alt="Alt">Safe p </p> acc')

    def test_empty_tags(self):
        self.assertSanitize('<p alt="Alt">p</p><p alt="Alt">  </p><p style="color:red"></p><p></p>',
                            '<p alt="Alt">p</p><p alt="Alt">  </p>')

        self.assertSanitize('<b>some<span> </span>text</b>',
                             '<b>some<span> </span>text</b>')

        self.assertSanitize('<p>head</p><p><br></p><p>tail</p>',
                            '<p>head</p><p>tail</p>')

        self.assertSanitize('<p>head</p><p><b><i> <br />  </i></b></p><p>tail</p>',
                            '<p>head</p><p>tail</p>')

        self.assertSanitize('<p>head</p><p><b>mid<i></i></b></p><p>tail</p>',
                            '<p>head</p><p><b>mid</b></p><p>tail</p>')

        self.attrs['allow_tags'].append('div')
        self.assertSanitize('<div>text<br>text</div>',
                            '<div>text<br>text</div>')

    @unittest.skip('lxml does not provide css filtration')
    def test_safe_css(self):
        u'''Ensure that sanitizer does not remove safe css'''
        self.attrs['allowed_attributes'].append('style')
        res = self.sanitize('<p style="color: #000; background-color: red; font-size: 1.2em">p</p>')
        assert 'color: #000; background-color: red; font-size: 1.2em' in res

    def test_allowed_classes(self):
        self.attrs['allow_classes']['p'] = ['yellow']
        self.attrs['allow_classes']['b'] = lambda x: 'b' in x

        self.assertSanitize('<p class="yellow green">',
                            '<p class="yellow"></p>')

        self.assertSanitize('<sup class="yellow green" title="Alt">a</sup>',
                            '<sup title="Alt">a</sup>')

        self.assertSanitize('<b class="has_b has_c">a</b>',
                            '<b class="has_b">a</b>')

    def test_tags_sticking(self):
        res = self.sanitize('<p>a</p> <p>b</p>')
        self.assertEqual(res, '<p>a</p> <p>b</p>')
        res = self.sanitize('<b>a</b> <b>b</b>')
        self.assertEqual(res, '<b>a</b> <b>b</b>')
        res = self.sanitize('<brbr>a</brbr> <p>b</p>')
        self.assertEqual(res, 'a <p>b</p>')
        res = self.sanitize('<p><brbr>a</brbr> <brbr>b</brbr></p>')
        self.assertEqual(res, '<p>a b</p>')

    @unittest.skip('not supported')
    def test_autoclosing_attrs_xhtml(self):
        self.attrs['method'] = 'xhtml'
        res = self.sanitize('<br><hr>b ')
        self.assertEqual(res, '<br /><hr />b')

    def test_autoclosing_attrs_html(self):
        self.attrs['drop_empty_tags'] = []
        res = self.sanitize('<br><hr>b <p>')
        self.assertEqual(res, '<br><hr>b <p></p>')

    def test_remove_empty_a(self):
        self.assertSanitize('<a href="moo">BLABLA</a> <a>txt <span>foo</span></a>',
                            '<a href="moo">BLABLA</a> txt <span>foo</span>')
        self.assertSanitize('<p><a>run</a><b><a>bar</a></b></p>',
                            '<p>run<b>bar</b></p>')

    @unittest.skip('lxml does not provide css filtration')
    def test_unsafe_css(self):
        u'''Special test for html5: html5lib has very ultimate css cleanup with gauntlets'''
        self.attrs['allowed_attributes'].append('style')
        res = self.sanitize('<p style="background: url(javascript:void); '
                       'color: #000; width: e/**/xpression(alert());">p</p>')
        self.assertEqual(res, '<p>p</p>')

    def test_plain_text(self):
        res = self.sanitize('Some plain text')
        self.assertEqual(res, 'Some plain text')

    def test_empty_strings(self):
        res = self.sanitize('')
        self.assertEqual(res, '')
        res = self.sanitize('\t    \n')
        self.assertEqual(res, '')

    def test_on_real_data(self):
        '''
            Compare with logged genshi output to ensure that there are no
            new errors
        '''
        return None
        skips = 10
        if os.path.isdir('clean_html'):
            self.attrs['string_callbacks'] = [html.remove_TinyMCE_trash,
                                              html.strip_empty_tags_nested,
                                              spaceless]
            for dir, dirs, files in os.walk('clean_html'):
                for file in filter(lambda x: x.endswith('.in'), files):
                    path = os.path.join(dir, file)
                    in_ = open(path, 'r').read().decode('utf-8')
                    out = open(path[:-3] + '.out', 'r').read().decode('utf-8')
                    out = html.remove_TinyMCE_trash(out) # Old sanitizer can't do this
                    #out = self.sanitize(out).strip()

                    res = self.sanitize(in_).strip()
                    if res != out:
                        if skips < 10:
                            print in_, '\n----------\n', res + '---\n!=\n' +  out + '---\n\n\n'
                        skips -= 1
                        if not skips:
                            return
                    #print "asserted"

    def test_no_initial_data(self):
        self.attrs = {}
        res = self.sanitize('a<p color: #000" class="2">p</p><script></script>')
        self.assertEqual(res, 'a<p>p</p>')

    @unittest.skip('lxml does not support this option')
    def test_escaping(self):
        self.attrs['escape_invalid_tags'] = True
        res = self.sanitize('a<p>p</p><script>alert()</script>')
        self.assertEqual(res, 'a<p>p</p>&lt;script&gt;alert()&lt;/script&gt;')

    def test_tags_to_wrap(self):
        self.attrs['tags_to_wrap'] = ['b', 'i', 'br']
        self.attrs['wrap_inline_tags'] = True

        self.assertSanitize("head<b>bold</b>tail",
                            "<p>head<b>bold</b>tail</p>")

        self.assertSanitize("head<b>bold</b>boldtail<i>italic</i><p>par</p>tail",
                            "<p>head<b>bold</b>boldtail<i>italic</i></p><p>par</p><p>tail</p>")

        self.assertSanitize("<p>par</p><b>bla</b>text<p>blabla</p>",
                            "<p>par</p><p><b>bla</b>text</p><p>blabla</p>")

        self.assertSanitize("<p>par</p>text<b>bla</b>text<p>blabla</p>",
                             "<p>par</p><p>text<b>bla</b>text</p><p>blabla</p>")

        self.assertSanitize('first<br>second<br>third',
                            '<p>first</p><p>second</p><p>third</p>')

        self.assertSanitize('first<br>second<p>third</p>',
                             '<p>first</p><p>second</p><p>third</p>')

        self.assertSanitize('<p>first</p>tail<br>second<p>third</p>',
                             '<p>first</p><p>tail</p><p>second</p><p>third</p>')

    def test_tags_to_wrap_trailing_br(self):
        self.attrs['tags_to_wrap'] = ['b', 'i', 'br']
        self.attrs['wrap_inline_tags'] = True
        self.assertSanitize("<p>head</p><br> ",
                            "<p>head</p>")

    def test_tags_to_wrap_double_br(self):
        self.attrs['tags_to_wrap'] = ['b', 'i', 'br']
        self.attrs['wrap_inline_tags'] = True

        self.assertSanitize("head<br><br>tail",
                            "<p>head</p><p>tail</p>")

        self.assertSanitize("head<br> <br>tail",
                            "<p>head</p><p>tail</p>")

        self.assertSanitize("<br><br><br><br>", "")

    
    def test_split_paragraphs_by_br(self):
        self.attrs['tags_to_wrap'] = ['b', 'i', 'br']
        self.attrs['wrap_inline_tags'] = True
        self.attrs['drop_empty_tags'] = []

        self.assertSanitize("<p>head<br><br><br></p>",
                            "<p>head</p><p></p><p></p><p></p>")

        self.assertSanitize("<p>head<br>body<br>tail</p>",
                            "<p>head</p><p>body</p><p>tail</p>")

        self.assertSanitize("<p>head<br><b>body<sup>letters</sup></b><br><i>ta</i>il</p>",
                            "<p>head</p><p><b>body<sup>letters</sup></b></p><p><i>ta</i>il</p>")

    def test_wrap_inline_tags(self):
        self.attrs['tags_to_wrap'] = ['b', 'i', 'br']
        self.attrs['wrap_inline_tags'] = False
        self.assertSanitize('first<br>second<br>third',
                            'first<br>second<br>third')

    def test_p_not_allowed(self):
        self.attrs['tags_to_wrap'] = ['b', 'i', 'br']
        self.attrs['wrap_inline_tags'] = 'div'
        # replacing p with div in allow_tags
        self.attrs['allow_tags'].remove('p')
        self.attrs['allow_tags'].append('div')

        self.assertSanitize("head<br><br>tail",
                            "<div>head</div><div>tail</div>")

    def test_lambda_wrap_tag(self):
        self.attrs['tags_to_wrap'] = ['b', 'i', 'br']
        self.attrs['wrap_inline_tags'] = lambda:Element('span')
        self.assertSanitize("head<br><br>tail",
                            "<span>head</span><span>tail</span>")
        self.attrs['allow_tags'].remove('p')

    def test_no_wrap_tags(self):
        self.attrs['tags_to_wrap'] = ['b', 'i', 'br']
        self.attrs['wrap_inline_tags'] = True
        self.attrs['allow_tags'].remove('p')
        self.assertRaises(ValueError, self.sanitize, 'head<br><br>tail')

    # cannot create Cleaner with wrong parameters
    def test_create_cleaner_with_wrong_parameters(self):
        self.attrs['wrap_inline_tags'] = True
        self.attrs['allow_tags'].remove('p')
        self.assertRaises(ValueError, html.Cleaner, **self.attrs)


def spaceless(clean, **kwargs):
    clean = re.compile('\s+').sub(' ', clean)
    return clean.strip()


