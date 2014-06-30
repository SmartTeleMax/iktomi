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
        ('info.birth_date', '19.05.1986'),
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



.. _forms-fields-aggregare:

Aggregate Fields
----------------

The most significant feature of iktomi forms is ability to work with structured
data with nested values.

Using iktomi you can easily work with deep JSON-like structures (containing
lists and dictionaries), generate ORM objects, ORM object collections, and 
even ORM object collection inside other ORM object.

There are three common aggregate classes implemented in iktomi.

FieldSet
~~~~~~~~

`FieldSet` is representation of dictionary (or object with named attribute).

`FieldSet` contains a collection of various fields with different names,
converters and widgets. `FieldSet` is to combines values converted with child
fields into a dictionary or object::

    class MyForm(Form):
        fields = [
            FieldSet('name',
                     fields=[
                        Field('first_name'),
                        Field('last_name'),
                     ])
        ]

    raw_value = MultiDict([
        ('name.first_name', 'Jar Jar'),
        ('name.last_name', 'Binks'),
    ])

    form = MyForm()
    form.accept(raw_value)
    print form.python_data
    # {"name": {'first_name': 'Jar Jar', 'last_name': "Binks"}}

To get object of custom type as a result of `FieldSet` you can define a custom
converter for that field. The converter must implement dict-to-object
convertation rules in `to_python` method and object-to-dict convertation rules
in `from_python` method.

You can see `iktomi.unstable.forms.convs.ModelDictConv` as an example of custom
FieldSet converter.

And, of course, you can add extra validation rules to this converter.

FieldSet adds it's input name as prefix for child fields, joined with a dot.

FieldBlock
~~~~~~~~~~

`FieldBlock` is like `FieldSet`, but it does not form separate object.
Instead, it adds it's own key-value pairs to parent field's value,
as if they are not wrapped in separate field.

`FieldBlock` is used for visually group fields or
for purposes of combined validation of those fields::

    class MyForm(Form):
        fields = [
            FieldBlock(None,
                     fields=[
                        Field('first_name'),
                        Field('last_name'),
                     ])
        ]

    raw_value = MultiDict([
        ('first_name', 'Jar Jar'),
        ('last_name', 'Binks'),
    ])

    form = MyForm()
    form.accept(raw_value)
    print form.python_data
    # {'first_name': 'Jar Jar', 'last_name': "Binks"}

Combined validation of nested fields is also easy to implement::

    def validate(field_block, value):
        if not (value['first_name'] or value['last_name']):
            raise convs.ValidationError('specify first or last name')
        return value

    FieldBlock(None,
               fields=[
                   Field('first_name'),
                   Field('last_name'),
               ],
               conv=FieldBlock.conv(validate))

FieldBlock does not affect on input names of child fields. It is named as if
they are children of FieldBlock's parent.


FieldList
~~~~~~~~~

`FieldList` represent a list (basically infinite) of identical fields.

`FieldList` creates instances of child field for each value list item.
Their input name is equal to FieldList's input name joined by a dot with 
value index in a list.

`FieldList` stores indexes of it's values in raw data, to use them to find
data of nested fields. The order of values in python_data depends on order of
indices of values in raw data.

Here is an example::

    class MyForm(Form):
        fields = [
            FieldList(
                'characters',
                field=FieldSet(None,
                     fields=[
                        Field('first_name'),
                        Field('last_name'),
                     ]))
        ]

    raw_value = MultiDict([
        ('characters.1.first_name', 'Jar Jar'),
        ('characters.2.last_name', 'Binks'),
    ])

    form = MyForm()
    form.accept(raw_value)
    print form.python_data
    # {'characters': [{'first_name': 'Jar Jar', 'last_name': 'Binks'},
    #                 {'first_name': 'Jabba', 'last_name': 'Hutt'}]}



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

Permissions propagate from parent fields (or form) to their children: child
field permissions are subset of it's parent permissions.

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

:ref:`See more<forms-perms>` about permission customization.


