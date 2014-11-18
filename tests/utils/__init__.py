# -*- coding: utf-8 -*-

import unittest, json
from iktomi.utils import (
    quoteattr, quoteattrs, quote_js, weakproxy,
    cached_property, cached_class_property,
)


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

    def test_cached_property(self):
        class C(object):
            def __init__(self):
                self.c = 0
            @cached_property
            def p(self):
                self.c += 1
                return 'a'
        self.assertIsInstance(C.p, cached_property)
        obj = C()
        self.assertEqual(obj.p, 'a')
        self.assertEqual(obj.c, 1)
        self.assertEqual(obj.p, 'a')
        self.assertEqual(obj.c, 1)
        del obj.p
        self.assertEqual(obj.p, 'a')
        self.assertEqual(obj.c, 2)
        obj = C()
        obj.p = 'b'
        self.assertEqual(obj.p, 'b')
        self.assertEqual(obj.c, 0)
        del obj.p
        self.assertEqual(obj.p, 'a')
        self.assertEqual(obj.c, 1)

    def test_cached_class_property(self):
        def create_C():
            class C(object):
                c = 0
                @cached_class_property
                def p(cls):
                    cls.c += 1
                    return 'a'
            return C
        C = create_C()
        obj = C()
        self.assertEqual(obj.p, 'a')
        self.assertEqual(C.c, 1)
        self.assertEqual(obj.p, 'a')
        self.assertEqual(C.c, 1)
        self.assertEqual(C.p, 'a')
        self.assertEqual(C.c, 1)
        C = create_C()
        obj = C()
        self.assertEqual(C.p, 'a')
        self.assertEqual(C.c, 1)
        self.assertEqual(obj.p, 'a')
        self.assertEqual(C.c, 1)

#    def test_cached_property_attribute_error(self):
#        class C(object):
#            @cached_property
#            def p(self):
#                return self.c
#
#        c = C()
#        self.assertRaises(Exception, hasattr, c, 'p')
