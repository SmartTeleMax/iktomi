from sqlalchemy.ext import declarative


class AutoTableNameMeta(declarative.DeclarativeMeta):

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


def table_args_meta(table_args):

    class TableArgsMeta(declarative.DeclarativeMeta):

        def __init__(cls, name, bases, dict_):
            # Do not extend base class
            if '_decl_class_registry' not in cls.__dict__:
                if cls.__dict__.get('__tablename__') and \
                        not cls.__dict__.get('__abstract__', False):
                    ta = getattr(cls, '__table_args__', {})
                    if isinstance(ta, dict):
                        ta = dict(table_args, **ta)
                        cls.__table_args__ = ta
                    else:
                        assert isinstance(ta, tuple)
                        if ta and isinstance(ta[-1], dict):
                            tad = dict(table_args, **ta[-1])
                            ta = ta[:-1] + dict(table_args, **ta[-1])
                        else:
                            tad = dict(table_args)
                        cls.__table_args__ = ta + (tad,)
            super(TableArgsMeta, cls).__init__(name, bases, dict_)

    return TableArgsMeta
