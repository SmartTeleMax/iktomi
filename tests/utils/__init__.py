# -*- coding: utf-8 -*-

import unittest, json
from iktomi.utils import quoteattr, quoteattrs, quote_js, weakproxy


class Tests(unittest.TestCase):

    def test_quoteattr(self):
        for src, dst in [('', '""'),
                         ('abc', '"abc"'),
                         ('"', '"&quot;"')]:
            self.assertEqual(quoteattr(src), dst)

    def test_quoteattrs(self):
        for src, dst in [({}, ''),
                         ({'a': u'abc', 'b': u'bcd'}, u'a="abc" b="bcd"')]:
            self.assertEqual(quoteattrs(src), dst)

    def test_quote_js(self):
        # Any idea for better test? json.loads() can't be used since the result
        # doesn't conform(?) JSON spec while being correct JavaScript string.
        # eval() seems OK except for "\r" removal.
        bad_chars = '\n\r\'"<>&'
        quoted = quote_js(u'\\\n\r\'"<>&')
        for char in bad_chars:
            self.assertNotIn(char, quoted)

    def test_weakproxy(self):
        # Immutable objects that can't be weakly referenced
        o = object()
        self.assertIs(weakproxy(o), o)
        # The rest objects
        class C(object):
            pass
        o = C()
        p = weakproxy(o)
        o.a = object()
        self.assertIs(p.a, o.a)
        del o
        with self.assertRaises(ReferenceError):
            p.a
