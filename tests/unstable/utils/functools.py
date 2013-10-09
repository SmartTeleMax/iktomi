import unittest, inspect
from iktomi.unstable.utils.functools import return_locals


class Tests(unittest.TestCase):

    def test_return_locals(self):
        def test_func(a, b=1, *args, **kwargs):
            '''Test function'''
            c = 2
        decorated = return_locals(test_func)
        self.assertEqual(test_func.__name__, decorated.__name__)
        self.assertEqual(test_func.__doc__, decorated.__doc__)
        d = decorated(0)
        self.assertIs(type(d), dict)
        self.assertEqual(d, {'c': 2})
