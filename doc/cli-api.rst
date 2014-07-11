:tocdepth: 1

Cli Reference
===============

.. module:: iktomi.cli.base

Base
----

manage
~~~~~~

.. autofunction:: iktomi.cli.base.manage

Cli
~~~

.. autoclass:: iktomi.cli.base.Cli
    :members:

    .. automethod:: __call__

.. autoclass:: iktomi.cli.lazy.LazyCli


Development Server
------------------

.. autoclass:: iktomi.cli.app.App
    :members:


FCGI Server
-----------

.. autoclass:: iktomi.cli.fcgi.Flup
    :members:


SQLAlchemy
----------

.. autoclass:: iktomi.cli.sqla.Sqla
    :members:

