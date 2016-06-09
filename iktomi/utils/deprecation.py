import warnings, functools

def deprecated(comment=None):
    '''
    This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used. Usage::

        @deprecated()
        def foo():
            pass

    or::

        @deprecated('Use bar() instead.')
        def foo():
            pass
    '''
    def deco(func):
        @functools.wraps(func)
        def new_func(*args, **kwargs):
            message = "Call to deprecated function {}.".format(func.__name__)
            if comment is not None:
                message += ' ' + comment
            warnings.warn(message, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return new_func
    return deco
