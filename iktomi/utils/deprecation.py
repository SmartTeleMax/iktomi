import warnings, functools

def deprecated(func_or_comment):
    '''This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.'''
    def deco(func):
        @functools.wraps(func)
        def new_func(*args, **kwargs):
            message = "Call to deprecated function %s." % func.__name__
            if comment is not None:
                message += ' ' + comment
            warnings.warn(message, category=DeprecationWarning)
            return func(*args, **kwargs)
        return new_func
    if isinstance(func_or_comment, basestring):
        comment = func_or_comment
        return deco
    else:
        comment = None
        return deco(func_or_comment)
