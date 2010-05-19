Forms API: Fields
=========

.. _insanities-forms-widgets:

.. toctree::
   :maxdepth: 2

* :ref:`Module description<insanities-forms-widgets>`
* :ref:`Widget <insanities-Widget>`
* :ref:`Some predefined widgets <insanities-predefined-widgets>`

Module Description
------------------

.. automodule:: insanities.forms.fields



.. _insanities-Widget:

Widget
^^^^^^
.. autoclass:: insanities.forms.widgets.Widget(\[template][, media][, classname][, \**kwargs])
   :members:



.. _insanities-Select:

Select
^^^^^^
.. autoclass:: insanities.forms.widgets.Select(\[size][, null_label][, \**kwargs])
   :members:

.. autoclass:: insanities.forms.widgets.CheckBoxSelect(\[\**kwargs])
   :members:

.. autoclass:: insanities.forms.widgets.ReadonlySelect(\[\**kwargs])
   :members:



.. _insanities-GroupedSelect:

GroupedSelect
^^^^^^^^^^^^^
.. autoclass:: insanities.forms.widgets.GroupedSelect(\[\**kwargs])
   :members:



.. _insanities-TinyMce:

TinyMce
^^^^^^^
.. autoclass:: insanities.forms.widgets.TinyMce(\[buttons][, plugins][, browsers][, cfg][, content_css][, compress][, add_plugins][, add_buttons][, drop_buttons][, \**kwargs])
   :members:



.. _insanities-CharDisplay:

CharDisplay
^^^^^^^^^^^
.. autoclass:: insanities.forms.widgets.CharDisplay(\[escape][, getter][\**kwargs])
   :members:



.. _insanities-predefined-widgets:

Some predefined widgets
^^^^^^^^^^^^^^^^^^^^^^^
There are some :class:`Widget <insanities-Widget>` subclasses
just defining their own templates and classnames.

.. autoclass:: insanities.forms.widgets.TextInput(\[\**kwargs])
   :members:


.. autoclass:: insanities.forms.widgets.HiddenInput(\[\**kwargs])
   :members:


.. autoclass:: insanities.forms.widgets.PasswordInput(\[\**kwargs])
   :members:


.. autoclass:: insanities.forms.widgets.Textarea(\[\**kwargs])
   :members:


.. autoclass:: insanities.forms.widgets.CheckBox(\[\**kwargs])
   :members:


.. autoclass:: insanities.forms.widgets.ImageView(\[\**kwargs])
   :members:


.. autoclass:: insanities.forms.widgets.Textarea(\[\**kwargs])
   :members:


