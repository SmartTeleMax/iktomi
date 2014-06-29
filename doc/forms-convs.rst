Converters
==========

`iktomi.forms.convs.Converter` instances are responsible for all staff related
to data validation and convertation. 

Converters implement :ref:`copy<form-copy>` interface.

Value convertation
------------------

Converter subclasses should define methods for transformations in two directions:

* `to_python` method accepts unicode value of user info, and returns value
  converted to python object of defined type. If the value can not be converted,
  it raises `iktomi.forms.convs.ValidationError`.
* `from_python` method accepts python object and returns corresponding unicode string.

ValidationError
---------------


Require Check
-------------

The most used feature is **require** check. If the converter has `require`
attribute set to `True`, it checks whether `to_python` result is an empty
value::

    Field('name',
          conv=convs.Char(required=True))


.. _forms-convs-listof:

ListOf and Multiple Values
--------------------------

Multiple values with same key in raw data are supported by `ListOf` converter::

    class MyForm(Form):

        fields = [
            Field('ids',
                  conv=ListOf(Int()))
        ]

    # ids=1&ids=2 =>
    # {"ids" [1, 2]}

Validators
----------

Additional validation and simple one-way convertation can be made by validators::

    Field('name',
          Char(strip, length(0, 100), required=True))

Handling readonly values
------------------------

Internationalization
--------------------

Converters for Aggregate Fields
-------------------------------

Collective validation
~~~~~~~~~~~~~~~~~~~~~

Custom FieldSet Value Type
~~~~~~~~~~~~~~~~~~~~~~~~~~

Converter implementations
-------------------------

Examples of converters are `Int`, `Char`, `Html`, `Bool`, `Date`, etc.

