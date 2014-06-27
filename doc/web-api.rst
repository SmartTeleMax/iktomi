:tocdepth: 1

Web Routing Reference
=====================

.. module:: iktomi.web.core

Basic handlers
--------------

.. autoclass:: iktomi.web.WebHandler
   :members:

   .. automethod:: __call__
   .. automethod:: __or__


.. autoclass:: iktomi.web.cases

   .. automethod:: __call__

.. autoclass:: iktomi.web.request_filter


.. module:: iktomi.web.filters

Builtin filters
---------------

.. autoclass:: iktomi.web.match
.. autoclass:: iktomi.web.prefix
.. autoclass:: iktomi.web.namespace
.. autoclass:: iktomi.web.subdomain(\*subdomains, name=None, primary=...)
.. autoclass:: iktomi.web.method
.. autoclass:: iktomi.web.by_method
.. autoclass:: iktomi.web.static_files


.. module:: iktomi.web.url_converters

Url converters
--------------

.. autoclass:: iktomi.web.url_converters.ConvertError
  :members:

.. autoclass:: iktomi.web.url_converters.Converter(default=NotSet)
.. autoclass:: iktomi.web.url_converters.String(min=None, max=None, default=NotSet)
.. autoclass:: iktomi.web.url_converters.Integer(default=NotSet)
.. autoclass:: iktomi.web.url_converters.Any(\*values, default=notSet)
.. autoclass:: iktomi.web.url_converters.Date(format="%Y-%m-%d", default=NotSet)


.. module:: iktomi.web.reverse

Reversing urls
--------------

.. autoclass:: iktomi.web.reverse.Reverse
   :members:

   .. automethod:: __call__
   .. automethod:: __getattr__
   .. automethod:: __str__

.. autoclass:: iktomi.web.reverse.Location


.. module:: iktomi.web.url

URL object
----------

.. autoclass:: iktomi.web.URL(path, query=None, host=None, port=None, schema=None, show_host=True)
    :members:


.. module:: iktomi.web.app

WSGI application
----------------

.. autoclass:: iktomi.web.Application
    :members:

    .. automethod:: __call__


.. autoclass:: iktomi.web.AppEnvironment
    :members:


