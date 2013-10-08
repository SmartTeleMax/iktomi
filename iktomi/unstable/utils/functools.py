from __future__ import absolute_import

import sys, functools


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
        return frames.pop(0).f_locals
    return wrap
