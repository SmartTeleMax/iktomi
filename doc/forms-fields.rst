Fields
======

Field in iktomi are basic concept representing a single item in data model.

It can be atomic data (string, integer, boolean) or data aggregated from
collection of other fields (`FieldList` or `FieldSet`, see below).
Atomic values correspond to `Field` class.

Field Naming
------------

Each field has a name. Name is used to get a value from raw data and as
key in resulting value dictionary. Name used to lookup in raw data is
`Field.input_name`, it is calculated as input_name of parent field joined by a
dot with the name of the field. 

Data that has no related field, is not present in python value.

Here is example of form without convertation and validation just to show how
field naming works::

    class MyForm(Form):

        fields = [
            Field('name'),
            FieldSet('info', fields=[
                Field('address'),
                Field('birth_date'),
            ]),
        ]

    raw_value = MultiDict([
        ('name', 'John'),
        ('info.address', 'Moscow'),
        ('info.birth_date, '19.05.1986'),
        ('info.more', 'This value is ignored'),
    ])

    form = MyForm()
    form.accept(raw_value)
    print form.python_data
    # {"name": "John",
    #  "info": {"address": "Moscow",
    #           "birth_date": "19.05.1986"}}

Also field name can be used to retrieve a field object from form or from
parent fields. If there are nested fields, those values are joined by dot::

    name_field = form.get_field('name')
    address_field = form.get_field('info.address')
    birth_field = form.get_field('info').get_field('birth_date')

Name of field should be unique throught it's neighbours. 

Converters and Widgets
----------------------

Two main properties of the field are `BaseField.conv`, defining convertation and
validation rules, and `BaseField.widget`, defining how widget is rendered to
HTML.

See more in :ref:`Converters<forms-convs>` and :ref:`Widgets<forms-widgets>`
sections.

Scalar and Multiple Fields
--------------------------

Iktomi forms have a way to MultiDict feature of having multiple values on the
same key. It is implementes by `ListOf` converter.

Fields having `ListOf` converter are marked as multiple. This means they always
return a list, each value of this list is converted by `ListOf.conv` converter.

Empty and defult values of multiple fields is empty list, while for scalar
fields it is `None`.

See :ref:`ListOf<forms-convs-listof>` for details.

Setting Initial Value
---------------------

Initial value of the field is calculated as follows:

* If the key equal to field's name is present in parent's initial value,
  it is used.
* If `BaseField.get_initial` is redefined, it is called and the result is used.
* If `BaseField.initial` is defined, it is used.
* Otherwise field initial value is set to empty value: `None` for scalar field
  and empty list for multiple field.


Access to Converted and Raw Values
----------------------------------

Access to current field value is provided by two properties: `raw_value` -
actual field raw (unconverted, result of `from_python`) and
`clean_value` - actual field converted value.

Raw data is stored in `Form` instance and actual clean value is stored directly
in the field.

Field instances are responsible for raw and clean value consistency with
current form state.

They fill `raw_data` with initial value reflection on form initialization
and they fill `raw_data` with actual validated value reflection during
validation process. Raw data is managed by `set_raw_value` method.

And `clean_value` is managed by `accept` method, the result of converter call is
set to `self.clean_value`.

These methods are already implemented for all fields provided by default and 
done automatically. But if you want to implement your own field class with 
specific data flow, you should carefully handle data consistency.

Field permissions
-----------------

Iktomi provides a simple but flexible permission system. Permissions can be set
in UNIX-like way by string where every single letter defines a permission::

    Field('name', permissions="rw")

Two permissions supported by default are read (`r`) and write (`w`).

Read permission allows field to be rendered.

Write permission allows assign a field value to convertation result. If 
the field has no `'w'` permission, it can not be changed by `form.accept`
method.

Permission can be set explicitly by passing `permissions` argument to `Field` or
by defining a custom permission getter object. For example, if you want a field
to be accessible only for several users, you can define your own subclass of 
`FieldPerm` and pass it to the field::

    Field('name', perm_getter=UserBasedFieldAuth())

:ref:`See more<forms-perms>`.

Aggregate Fields
----------------

FieldSet
~~~~~~~~

FieldBlock
~~~~~~~~~~

FieldList
~~~~~~~~~

