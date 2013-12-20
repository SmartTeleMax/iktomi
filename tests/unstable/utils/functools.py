import unittest, sys, inspect, cProfile
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

    def test_return_locals_profile_events(self):
        '''Insure profile function gets events for function decorated with
        return_locals at least the same as for function itself.'''
        def collect_events(func):
            events = []
            def tracer(frame, event, args):
                events.append((frame.f_code, event))
            old_tracer = sys.getprofile()
            sys.setprofile(tracer)
            try:
                func()
            finally:
                sys.setprofile(old_tracer)
            return events
        def inner():
            return 2
        def outer():
            a = 1
            b = inner()
        events1 = set(collect_events(outer))
        events2 = set(collect_events(return_locals(outer)))
        self.assertTrue(events2.issuperset(events1))

    def test_return_locals_debugger_events(self):
        '''Insure debugging function gets events for function decorated with
        return_locals at least the same as for function itself.'''
        def collect_events(func):
            events = []
            def tracer(frame, event, args):
                events.append((frame.f_code, event))
                return tracer
            old_tracer = sys.gettrace()
            sys.settrace(tracer)
            try:
                func()
            finally:
                sys.settrace(old_tracer)
            return events
        def inner():
            return 2
        def outer():
            a = 1
            b = inner()
        events1 = set(collect_events(outer))
        events2 = set(collect_events(return_locals(outer)))
        self.assertTrue(events2.issuperset(events1))

    def test_return_locals_cProfile(self):
        '''Insure code using return_locals is profilable with cProfile.'''
        @return_locals
        def func():
            pass
        cProfile.runctx('func()', {'func': func}, {})
