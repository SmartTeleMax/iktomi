from __future__ import absolute_import

import sys, functools, inspect


def return_locals(func):
    '''Modifies decorated function to return its locals'''

    @functools.wraps(func)
    def wrap(*args, **kwargs):
        frames = []

        def tracer(frame, event, arg): # pragma: no cover
            # coverage does not work in this function because the tracer
            # is deactivated here
            frames.append(frame)
            sys.settrace(old_tracer)
            if old_tracer is not None:
                return old_tracer(frame, event, arg)

        old_tracer = sys.gettrace()
        # tracer is activated on next call, return or exception
        sys.settrace(tracer)
        try:
            func(*args, **kwargs)
        finally:
            sys.settrace(old_tracer)
        assert len(frames) == 1
        argspec = inspect.getargspec(func)
        argnames = list(argspec.args)
        if argspec.varargs is not None:
            argnames.append(argspec.varargs)
        if argspec.keywords is not None:
            argnames.append(argspec.keywords)
        return {name: value for name, value in frames.pop(0).f_locals.items()
                if name not in argnames}

    return wrap
