# -*- coding: utf-8 -*-
import six
import logging
from importlib import import_module
from sqlalchemy import create_engine


def multidb_binds(databases, package=None, engine_params=None):
    '''Creates dictionary to be passed as `binds` parameter to
    `sqlalchemy.orm.sessionmaker()` from dictionary mapping models module name
    to connection URI that should be used for these models. Models module must
    have `metadata` attribute. `package` when set must be a package or package
    name for all models modules.'''
    engine_params = engine_params or {}
    if not (package is None or isinstance(package, six.string_types)):
        package = getattr(package, '__package__', None) or package.__name__
    binds = {}
    for ref, uri in databases.items():
        md_ref = '.'.join(filter(None, [package, ref]))
        md_module = import_module(md_ref)
        try:
            metadata = md_module.metadata
        except AttributeError:
            raise ImportError(
                'Cannot import name metadata from module {}'.format(md_ref))
        engine = create_engine(uri, **engine_params)
        # Dot before [name] is required to allow setting logging level etc. for
        # all them at once.
        engine.logger = logging.getLogger('sqlalchemy.engine.[%s]' % ref)
        for table in metadata.sorted_tables:
            binds[table] = engine
    return binds
