import six
import inspect, weakref
from sqlalchemy.ext.declarative import declared_attr
from iktomi.unstable.utils.functools import return_locals


def declared_mixin(*bases):
    '''Create mix-in class with all assignments turned into methods decorated
    with declared_attr. Usage:

        @declared_mixin
        def FactoryFunction():

    or with base mix-in class[es]:

        @declared_mixin(BaseMixIn1, BaseMixIn2)
        def FactoryFunction():

    For example:

        @declared_mixin
        def WithParent():
            parent_id = Column(ForeignKey(Parent.id))
            parent = relationship(Parent)

    is equivalent to

        class WithParent(object):
            @declared_attr
            def parent_id(cls):
                return Column(ForeignKey(Parent.id))
            @declared_attr
            def parent(cls):
                return relationship(Parent)
    '''

    def wrapper(func):
        attrs = weakref.WeakKeyDictionary()
        def create_descriptor(name):
            def get_attr(cls):
                if cls not in attrs:
                    # Call func only once per class
                    attrs[cls] = return_locals(func)()
                return attrs[cls][name]
            get_attr.__name__ = name
            return declared_attr(get_attr)
        dict_ = {name: create_descriptor(name)
                 for name in six.get_function_code(func).co_varnames}
        dict_['__doc__'] = func.__doc__
        return type(func.__name__, bases, dict_)

    if len(bases)==1 and not isinstance(bases[0], type):
        # Short form (without bases) is used
        func = bases[0]
        bases = ()
        return wrapper(func)
    else:
        return wrapper
