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

In the case `ValidationError` occured, converter returns field's
initial/last valid value. In other words, the value is reverted to it's last
valid state, basically it is initial state.

.. _iktomi-forms-convs-by_field:

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

`ListOf` gets all values by field's key from raw data `MultiDict`, applies
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

The `multiple` property of fields and widgets having ListOf converter, is equal
to `True`.


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

Internationalization
--------------------

Iktomi implements very basic internationalization support. There are `N_` and
`M_` markers for single and plural translatable strings respectively.

There is no complex mechanics with threadlocals or other things allowing to
transparently "in place" and lazy translate these strings. Iktomi by default supports
only translation of `ValidationError` messages before they are added in
`form.errors`.

For single messages `env.gettext` is called, and for plural ones `env.ngettext` is
called. You must provide these methods in your `Application` subclass.

Here is an example of how plural merker works. Dictionary formatting with `%` is
used and a key `M_.count_field` is used as count indicator to `ngettext`::

    message = M_(u'must be less than %(max)d symbol',
                 u'must be less than %(max)d symbols',
                 count_field="max")
    def validate(conv, value):
        max_length = get_max_length(conv)
        if len(value) > max_length:
            message = message % dict(max=max_length)
            raise convs.ValidationError(message)
        return value


Converters for Aggregate Fields
-------------------------------

.. _iktomi-forms-convs-fsvalidation:

Collective validation
~~~~~~~~~~~~~~~~~~~~~

`FieldSet` and `FieldBlock` converters are good place to implement a complex
validation rules, including data from more than one field.

You can implement them in to_python method of converter or in a validator. To
access a value of child field just get it from actual dict by a field name::

    #def validate(conv, value):
    def to_python(self, value):
        if value['field1'] == value['field2']:
            raise ValidationError('values must not be equal')
        return value

:ref:`ValidationError.by_field feature<iktomi-forms-convs-by_field>` also can be useful here.

.. _iktomi-forms-convs-fsobject:

Custom FieldSet Value Type
~~~~~~~~~~~~~~~~~~~~~~~~~~

To get a custom object as a clean value of FieldSet, you can define own
`Converter` subclass implementing transformations from an object to dictionary
(in `from_python` method) and from dictionary to an object (in `to_python`).

The most basic example of converter of this kind::

    class ObjConv(Converter):

        def from_python(self, value):
            result = {}
            # in case there are nested FieldBlock fields, always use field.field_names
            # to get a list of fields directly contained in the value
            field_names = sum([x.field_names for x in self.field.fields], [])
            for field_name in field_names:
                result[field_name] = getattr(value, field_name)
            return result

        def to_python(self, value):
            return self.model(** value)

You can see `iktomi.unstable.forms.convs.ModelDictConv` as an example of custom
FieldSet converter.

Converter implementations
-------------------------

Examples of converters are `Int`, `Char`, `Html`, `Bool`, `Date`, etc.

