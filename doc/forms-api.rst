:tocdepth: 1

Forms Reference
===============

.. module:: iktomi.forms.form

Forms
-----

.. autoclass:: iktomi.forms.Form
   :members:


.. module:: iktomi.forms.fields

Fields
------

.. autoclass:: iktomi.forms.fields.BaseField
    :members:

    .. automethod:: __call__


.. autoclass:: iktomi.forms.fields.Field
  :members:


.. autoclass:: iktomi.forms.fields.FieldSet
  :members:


.. autoclass:: iktomi.forms.fields.FieldBlock
  :members:


.. autoclass:: iktomi.forms.fields.FieldList
  :members:


.. autoclass:: iktomi.forms.fields.FileField
  :members:


.. module:: iktomi.forms.convs

Converters
----------

.. autoexception:: iktomi.forms.convs.ValidationError
    :members:

.. autoclass:: iktomi.forms.convs.Converter
    :members:

    .. automethod:: __call__


.. autoclass:: iktomi.forms.convs.Char
    :members:

    .. automethod:: clean_value
    .. autoattribute:: strip


.. autoclass:: iktomi.forms.convs.Int
    :members:

.. autoclass:: iktomi.forms.convs.Bool
    :members:

.. autoclass:: iktomi.forms.convs.DisplayOnly
    :members:

.. autoclass:: iktomi.forms.convs.EnumChoice
    :members:

.. autoclass:: iktomi.forms.convs.BaseDatetime
    :members:

.. autoclass:: iktomi.forms.convs.Datetime
    :members:

.. autoclass:: iktomi.forms.convs.Date
    :members:

.. autoclass:: iktomi.forms.convs.Time
    :members:

.. autoclass:: iktomi.forms.convs.SplitDateTime
    :members:

.. autoclass:: iktomi.forms.convs.Html
    :members:

.. autoclass:: iktomi.forms.convs.List
    :members:

.. autoclass:: iktomi.forms.convs.ListOf
    :members:

.. autoclass:: iktomi.forms.convs.SimpleFile
    :members:


Validators and filters
----------------------

.. autofunction:: iktomi.forms.convs.validator
.. autofunction:: iktomi.forms.convs.length
.. autofunction:: iktomi.forms.convs.between


.. module:: iktomi.forms.widgets

Widgets
-------

.. autoclass:: iktomi.forms.widgets.Widget
    :members:

    .. automethod:: __call__

.. autoclass:: iktomi.forms.widgets.TextInput
.. autoclass:: iktomi.forms.widgets.Textarea
.. autoclass:: iktomi.forms.widgets.HiddenInput
.. autoclass:: iktomi.forms.widgets.PasswordInput
.. autoclass:: iktomi.forms.widgets.Select
    :members:

.. autoclass:: iktomi.forms.widgets.CheckBoxSelect
.. autoclass:: iktomi.forms.widgets.CheckBox
.. autoclass:: iktomi.forms.widgets.CharDisplay
.. autoclass:: iktomi.forms.widgets.FieldListWidget
.. autoclass:: iktomi.forms.widgets.FieldSetWidget
.. autoclass:: iktomi.forms.widgets.FieldBlockWidget
.. autoclass:: iktomi.forms.widgets.FileInput
