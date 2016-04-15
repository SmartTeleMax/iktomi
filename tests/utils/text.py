# -*- coding: utf-8 -*-

__all__ = ['TextTests']

import unittest
from iktomi.utils.text import pare


class TextTests(unittest.TestCase):

    def test_pare(self):
        # XXX a quite strange function...
        #     Don't we want to limit result length to size including postfix length?
        self.assertEqual(pare('', 15, '_'), '')
        self.assertEqual(pare('Small text', 15, '_'), 'Small text')
        self.assertEqual(pare('A long text containing many words', 15, '_'), 'A long text_')
        self.assertEqual(pare('Averylongsingleword', 15, '_'), 'Averylongsingle_')
        self.assertEqual(pare('A verylongsingleword', 16, '_'), 'A verylongsingle_')
        self.assertEqual(pare('A verylong singleword', 16, '_'), 'A verylong_')

        self.assertEqual(pare('Spaces after text              ', 20, '_'), 'Spaces after text')
        self.assertEqual(pare('Space after edge', 11, '_'), 'Space after_')
        self.assertEqual(pare('Space before edge', 13, '_'), 'Space before_')

