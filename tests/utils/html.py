# -*- coding: utf-8 -*-
import unittest
import os
import re
from insanities.utils import html
from copy import deepcopy

class TestSanitizer(unittest.TestCase):
    '''Tests for sanitizer based on html5lib'''

    def setUp(self):
        self.attrs = {
            'allowed_elements': ['a', 'p', 'br', 'li', 'ul', 'ol', 'hr', 'u', 'i', 'b',
                          'blockquote', 'sub', 'sup', 'span'],
            'allowed_attributes': ['href', 'src', 'alt', 'title', 'class', 'rel'],
            'drop_empty_tags': ['p', 'a', 'u', 'i', 'b', 'sub', 'sup'],
            'allowed_classes': {},
            'strip_whitespace': True,
        }

    def sanitize(self, text):
        return html.sanitize(text, **self.attrs)
        
    def test_safe_attrs(self):
        res = self.sanitize('<p notsafeattr="s" abbr="1" alt="Alt">Safe p</p>')
        self.assertEqual(res, '<p alt="Alt">Safe p</p>')

    def test_safe_tags(self):
        res = self.sanitize('<p alt="Alt">Safe p <script>bad_script()</script></p> <accept>acc</accept>')
        self.assertEqual(res, '<p alt="Alt">Safe p bad_script()</p> acc')

    def test_empty_tags(self):
        res = self.sanitize('<p alt="Alt">p</p><p alt="Alt">  </p><p></p>')
        self.assertEqual(res, u'<p alt="Alt">p</p> ')
        res = self.sanitize('<b>some<span> </span>text</b>')
        self.assertEqual(res, '<b>some<span> </span>text</b>')
        
    
    def test_safe_css(self):
        u'''Ensure that sanitizer does not remove safe css'''
        self.attrs['allowed_attributes'].append('style')
        res = self.sanitize('<p style="color: #000; background-color: red; font-size: 1.2em">p</p>')
        assert 'color: #000; background-color: red; font-size: 1.2em' in res
    
    def test_allowed_classes(self):
        self.attrs['allowed_classes']['p'] = ['yellow']
        self.attrs['allowed_classes']['b'] = lambda x: 'b' in x
        
        res = self.sanitize('<p class="yellow green">'
                            '<sup class="yellow green" title="Alt">a</sup></p>'
                            '<b class="has_b has_c">a</b>')
        self.assertEqual(res, '<p class="yellow"><sup title="Alt">a</sup></p>'
                              '<b class="has_b">a</b>')
    
    def test_tags_sticking(self):
        res = self.sanitize('<p>a</p> <p>b</p>')
        self.assertEqual(res, '<p>a</p> <p>b</p>')
        res = self.sanitize('<b>a</b> <b>b</b>')
        self.assertEqual(res, '<b>a</b> <b>b</b>')
        res = self.sanitize('<script>a</script> <p>b</p>')
        self.assertEqual(res, 'a <p>b</p>')
        res = self.sanitize('<p><script>a</script> <script>b</script></p>')
        self.assertEqual(res, '<p>a b</p>')

    def test_autoclosing_attrs_xhtml(self):
        self.attrs['method'] = 'xhtml'
        res = self.sanitize('<br><hr>b ')
        self.assertEqual(res, '<br /><hr />b')

    def test_autoclosing_attrs_html(self):
        self.attrs['method'] = 'html'
        self.attrs['drop_empty_tags'] = []
        res = self.sanitize('<br><hr>b <p>')
        self.assertEqual(res, '<br><hr>b <p></p>')
        
    def test_remove_empty_a(self):
        #Not implemented by genshi
        res = self.sanitize('<a href="moo">BLABLA</a> <a>txt <span>foo</span></a>'
                            's  <p><a>run</a><b><a>bar</a></b></p>')
        self.assertEqual(res, '<a href="moo">BLABLA</a> txt <span>foo</span>'
                              's <p>run<b>bar</b></p>')

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
    
    def test_escaping(self):
        self.attrs['escape_invalid_tags'] = True
        res = self.sanitize('a<p>p</p><script>alert()</script>')
        self.assertEqual(res, 'a<p>p</p>&lt;script&gt;alert()&lt;/script&gt;')
        
    
    
def spaceless(clean, **kwargs):
    clean = re.compile('\s+').sub(' ', clean)
    return clean.strip()

    
if __name__ == '__main__':
    unittest.main()
