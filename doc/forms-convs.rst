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
* Filters and validators provide extra validation and are called after 
  `to_python` method. :ref:`See below<forms-convs-validators>` for details.
* `from_python` method accepts python object and returns corresponding unicode string.

ValidationError
---------------

The common way for converter to indicate that given value can not be accepted is
to raise `ValidationError` from `to_python` method::

    def to_python(self, value):
        if not self.match(value):
            raise ValidationError(error_message)
        return value

If `ValidationError` was raised, the error is added to `form.errors` dictionary.
The key is current field's input name and the value is 

In the case of `ValidationError` converter returns field's default value (the
value is reverted).

Raise error for other field
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes you need to show error not on a field which is validating, or show
error on multiple fields on the same condition. In this case
`ValidationError.by_field` argument can be used.

Just pass in `by_field` kwarg a dict where a key is input_name of any field in the
form and a value is error message::

    raise convs.ValidationError(by_field={
            'name': 'Provide a name or a nickname',
            'nickname': 'Provide a name or a nickname'})

Relative field input names can be used. If a name starts with a dot,
`conv.field.get_field` will be used to get target field. If it starts with two
dots, `conv.field.parent.get_field` will be used, three dots -
`conv.field.parent.parent.get_field`, etc.

Why not to set `form.errors[field.input_name]` directly? Trust me, it is not
good idea! One reason is `conv.accept` silent mode, used to fill in 
initial values of the field and sometimes can be used to call converter as a function
without form attached and error handling. **Other reasons?**

Error messages redefinition
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Default converters support redefinition of default error messages.

Set `error_<type>` parameter to your own message template, for example::

    convs.Char(required=True,
               regex="\d{2}\.\d{2}\.\d{2}",
               error_regex='Should match YY.MM.DD',
               error_required='Do not forget this field!')


Require Check
-------------

The most used feature is **require** check. If the converter has `require`
attribute set to `True`, it checks whether `to_python` result is an empty
value::

    Field('name',
          conv=convs.Char(required=True))

Empty values are empty string, emty list, empty dict and `None`. If the result
value is equal to one of these values, `ValidationError` with
`conv.error_required` is raised.


.. _forms-convs-listof:

ListOf and Multiple Values
--------------------------

Multiple values with same key in raw data are supported by `ListOf` converter.

`ListOf` gets all values by field's key from raw data MultiDict, applies
`ListOf.conv` to each of them, and collects non-empty results
into a list. If ValidationError was raised in `ListOf.conv`, the value is also
ignored::

    class MyForm(Form):

        fields = [
            Field('ids',
                  conv=ListOf(Int()))
        ]

    # ids=1&ids=2&ids=x =>
    # {"ids" [1, 2]}

.. _forms-convs-validators:

Filters and validators:
-----------------------

Additional validation and simple one-way convertation can be made by validators::

    Field('name',
          Char(strip, length(0, 100), required=True))

Filters are functions performing additional validation and convertation 
after :meth:`to_python` method. The interface of filters is following::

    def filter_value(conv, value):
        if wrong(value):
            raise ValidationError(..)
        new_value = do_smth(value)
        return new_value

    convs.Char(filter_value, required=True)

Validators are shortcuts to filters that do no convertations, but  only
do assertions::

    @validator(error_message)
    def validate(conv, value):
        return is_valid(value)

Both filters and validators can be passed to converter as positional 
arguments and will be applied after :meth:`to_python` method and 
`required` check in order they are mentioned.


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

