Routing tools
=============

.. _insanities-web-routing:

.. toctree::
   :maxdepth: 2

* :ref:`Base classes <WebBaseClasses>`
   * :ref:`RequestHandler <RequestHandler>`
   * :ref:`Map <Map>`
   * :ref:`FunctionWrapper <FunctionWrapper>`
* :ref:`Default handlers <WebDefaultHandlers>`
   * :ref:`match <match>`
   * :ref:`method <method>`
   * :ref:`prefix <prefix>`
   * :ref:`subdomain <subdomain>`
   * :ref:`namespace <namespace>`
   * :ref:`Conf <Conf>`


.. _WebBaseClasses:

Base classes
------------

.. automodule:: insanities.web.core

.. _RequestHandler:

RequestHandler
^^^^^^^^^^^^^^
.. autoclass:: insanities.web.core.RequestHandler
   :members:


.. _Map:

Map
^^^
.. autoclass:: insanities.web.core.Map
   :members:


.. _FunctionWrapper:

FunctionWrapper
^^^^^^^^^^^^^^^
.. autoclass:: insanities.web.core.FunctionWrapper
   :members:


.. _WebDefaultHandlers:

Default handlers
----------------

.. _match:

match
^^^^^
.. autoclass:: insanities.web.filters.match
   :members:

.. _method:

method
^^^^^^
.. autoclass:: insanities.web.filters.method
   :members:


.. _prefix:

prefix
^^^^^^
.. autoclass:: insanities.web.wrappers.prefix
   :members:


.. _subdomain:

subdomain
^^^^^^^^^
.. autoclass:: insanities.web.wrappers.subdomain
   :members:


.. _namespace:

namespace
^^^^^^^^^
.. autoclass:: insanities.web.wrappers.namespace
   :members:


.. _Conf:

Conf
^^^^
.. autoclass:: insanities.web.wrappers.Conf
   :members:

