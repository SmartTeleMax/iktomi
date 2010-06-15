Different utilities used in project
===================================

.. _insanities-utils:

.. toctree::
   :maxdepth: 2

* :ref:`OrderedDict <OrderedDict>`
* :ref:`HTML Sanitarization <Sanitarization>`
* :ref:`URL handling <URLS>`


.. _OrderedDict:

OrderedDict
-----------

.. automodule:: insanities.utils.odict

OrderedDict Interface
^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: insanities.utils.odict.OrderedDict
   :members:

..
    S.. _MultiDict:

    SMultiDict
    S-----------

    S.. automodule:: insanities.utils.mdict

    SMultiDict Interface
    S^^^^^^^^^^^^^^^^^^^

    S.. autoclass:: insanities.utils.mdict.MultiDict
    S   :members: items, append, getfirst, getlast



.. _Sanitarization:

HTML Sanitarization
-------------------

.. automodule:: insanities.utils.html

Sanitizer
^^^^^^^^^

.. autoclass:: insanities.utils.html.Sanitizer
   :members:


.. _URLS:

URLs handling
-------------

.. automodule:: insanities.utils.url

URL
^^^

.. autoclass:: insanities.utils.url.URL(path\[query=None][host=None][port=None][schema=None])
   :members:

UrlTemplate
^^^^^^^^^^^

.. autoclass:: insanities.utils.url.UrlTemplate
   :members:
