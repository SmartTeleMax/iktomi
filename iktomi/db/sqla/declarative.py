# -*- coding: utf-8 -*-

'''Declarative metaclasses to incapsulate repeated code into base class. To
combine them you have to create a subclass. Example:

    TABLE_ARGS = {
        'mysql_engine': 'InnoDB',
        'mysql_default charset': 'utf8',
    }

    class Meta(AutoTableNameMeta, TableArgsMeta(TABLE_ARGS)):
        pass

    Base = declarative_base(name='Base', metaclass=Meta)

    class MyClass(Base):
        …

is equivalent to

    class MyClass(Base):
        __tablename__ = 'MyClass'
        __table_args__ = {
            'mysql_engine': 'InnoDB',
            'mysql_default charset': 'utf8',
        }
        …
'''

from sqlalchemy.ext import declarative
from ...utils.deprecation import deprecated


class AutoTableNameMeta(declarative.DeclarativeMeta):
    '''Declarative metaclass automatically giving the same name to table as
    mapped class. Example:

        Base = declarative_base(name='Base', metaclass=AutoTableNameMeta)

        class MyClass(Base):
            …

    is equivalent to

        Base = declarative_base(name='Base')

        class MyClass(Base):
            __tablename__ = 'MyClass'
            …
    '''

    def __init__(cls, name, bases, dict_):
        # Do not extend base class
        if '_decl_class_registry' not in cls.__dict__:
            # Lookup __dict__ and not attribute directly since __tablename__
            # should change on inheritance.
            if '__tablename__' not in cls.__dict__ and \
                    not cls.__dict__.get('__abstract__', False):
                cls.__tablename__ = name
            # XXX Commented untill we write the reason in comments
            #elif cls.__tablename__ is None:
            #    del cls.__tablename__
        super(AutoTableNameMeta, cls).__init__(name, bases, dict_)


def TableArgsMeta(table_args):
    '''Declarative metaclass automatically adding (merging) __table_args__ to
    mapped classes. Example:

        Meta = TableArgsMeta({
            'mysql_engine': 'InnoDB',
            'mysql_default charset': 'utf8',
        }

        Base = declarative_base(name='Base', metaclass=Meta)

        class MyClass(Base):
            …

    is equivalent to

        Base = declarative_base(name='Base')

        class MyClass(Base):
            __table_args__ = {
                'mysql_engine': 'InnoDB',
                'mysql_default charset': 'utf8',
            }
            …
    '''

    class _TableArgsMeta(declarative.DeclarativeMeta):

        def __init__(cls, name, bases, dict_):
            if (    # Do not extend base class
                    '_decl_class_registry' not in cls.__dict__ and 
                    # Missing __tablename_ or equal to None means single table
                    # inheritance — no table for it (columns go to table of
                    # base class)
                    cls.__dict__.get('__tablename__') and
                    # Abstract class — no table for it (columns go to table[s]
                    # of subclass[es]
                    not cls.__dict__.get('__abstract__', False)):
                ta = getattr(cls, '__table_args__', {})
                if isinstance(ta, dict):
                    ta = dict(table_args, **ta)
                    cls.__table_args__ = ta
                else:
                    assert isinstance(ta, tuple)
                    if ta and isinstance(ta[-1], dict):
                        tad = dict(table_args, **ta[-1])
                        ta = ta[:-1]
                    else:
                        tad = dict(table_args)
                    cls.__table_args__ = ta + (tad,)
            super(_TableArgsMeta, cls).__init__(name, bases, dict_)

    return _TableArgsMeta


table_args_meta = deprecated('Use TableArgsMeta instead.')(TableArgsMeta)
