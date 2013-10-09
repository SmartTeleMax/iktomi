from __future__ import absolute_import

import sys, functools, inspect


def return_locals(func):
    '''
        Wraps function, so it is executed and it's locals() are returned
    '''
    @functools.wraps(func)
    def wrap(*args, **kwargs):
        frames = []
        def tracer(frame, event, arg):
            sys.setprofile(oldprofile)
            frames.append(frame)

        oldprofile = sys.getprofile()
        # tracer is activated on next call, return or exception
        sys.setprofile(tracer)
        try:
            func(*args, **kwargs)
        finally:
            sys.setprofile(oldprofile)
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
