import unittest
from iktomi.utils import quoteattr, quoteattrs


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
