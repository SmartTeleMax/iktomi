Overview: Form Abstraction Layers
=================================

Form is abstraction designed to validate user form data and convert it to inner
representation form.

Iktomi forms can accept data in `webob.MultiDict`-like form (basically
`request.POST` and `request.GET` objects), and return it in form of any python
objects hierarchy, depending only on implementation. Basically it is structured
combination of python dicts and lists containing atomic values.

The most basic usage of forms is the following::

    from iktomi.forms.form import Form
    from iktomi.forms.fields import Field, FieldList

    class UncleForm(Form):
        fields = [
            Field('name'),
            FieldList('nephews', field=FieldSet(None, fields=[
                Field('name'),
            ])),
        ]

    def process_form(request):
        form = UncleForm()
        if form.accept(request.POST):
            render_somehow(form.python_data)
            # {"name": "Scrooge",
            #  "nephews": [{"name": "Huey"},
            #              {"name": "Dewey"},
            #              {"name": "Louie"}]}
        else:
            render_somehow(form, form.errors)

Iktomi form implementation contains of few abstraction layers:

Forms
-----

`iktomi.forms.form.Form` subclasses contain a scheme of validated data as list
of fields. Instances of these classes provide an interface to work with entire
form, such as: validate the data (`Form.accept`), render the entire form
(`Form.render`). Also they store common form data: initial, raw and resulting
values, environment, errors occured during validation.

Fields
------

`iktomi.forms.fields.BaseField` instances represent one node in data scheme.
It can be atomic data (string, integer, boolean) or data aggregated from
collection of other fields (`FieldList` or `FieldSet`, see below).
Atomic values correspond to `Field` class.

Each field has a name. Name is a key in resulting value dictionary.

Also there are a few auxillary attributes like `label`, `hint`.

Finally, the main options of `BaseField` instances are converter and widget
objects.

:ref:`See more<forms-form>`.

Converters
----------

`iktomi.forms.convs.Converter` instances are responsible for all staff related
to data validation and convertation. Converter subclasses should define
methods for transformations in two directions:

* `to_python` method accepts unicode value of user info, and returns value
  converted to python object of defined type. If the value can not be converted,
  it raises `iktomi.forms.convs.ValidationError`.
* `from_python` method accepts python object and returns corresponding unicode string.

Examples of converters are `Int`, `Char`, `Html`, `Bool`, `Date`, etc.

Converters support few interesting additional features.

The most used feature is **require** check. If the converter has `require`
attribute set to `True`, it checks whether `to_python` result is an empty
value::

    Field('name',
          conv=convs.Char(required=True))

**Multiple** values are implemented by `ListOf` converter::

    class MyForm(Form):

        fields = [
            Field('ids',
                  conv=ListOf(Int()))
        ]

    # ids=1&ids=2 =>
    # {"ids" [1, 2]}

Additional validation and simple one-way convertation can be made by **validators**::

    Field('name',
          Char(strip, length(0, 100), required=True))

Widgets
-------

`iktomi.forms.widget.Widget` instances are responsible for visual representation
of an item.

The main method of widget is `render`, which is called to get HTML code of field
with actual value.

Widget can do some data preparations and finally it is rendered to template
named `widget.template` (by default, `jinja2` is used).

Examples of widgets are `TextInput`, `Textarea`, `Select`, `CheckBox`, 
`HiddenInput`, etc.


Aggregate Fields
----------------

Iktomi forms are very useful to validate and convert structured data with nested
values.

There are three basic subclasses of `BaseField`. Combining fields of
those classes, you can describe a scheme for nested JSON-like data (containing
lists and dictionaries). And you can easily describe any tree-like python objects
structure using custom `Converter` subclasses.

These classes are:

* `FieldSet` represent a collection of various fields with different names,
  converters and widgets. Purpose of `FieldSet` is to combine values into a
  dictionary or object (you can get an object of whatever type you want by
  defining your own converter for `FieldSet` with transformation rules to/from
  dictionary)::

    class MyForm(Form):
        fields = [
            FieldSet('name',
                     fields=[
                        Field('first_name'),
                        Field('last_name'),
                     ])
        ]

    # {"name": {'first_name': 'Jar Jar', 'last_name': "Binks"}}

* `FieldBlock` is like `FieldSet`, but it does not form separate object.
  Instead, it adds it's own values to parent field's value, as if they are not
  wrapped in separate field. `FieldBlock` is used for visually group fields or
  for purposes of combined validation of those fields::

    class MyForm(Form):
        fields = [
            FieldBlock(None,
                     fields=[
                        Field('first_name'),
                        Field('last_name'),
                     ])
        ]

    # {'first_name': 'Jar Jar', 'last_name': "Binks"}

* `FieldList` represent a list (basically infinite) of identical fields::

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

    # {'characters': [{'first_name': 'Jar Jar', 'last_name': 'Binks'},
    #                 {'first_name': 'Jabba', 'last_name': 'Hutt'}]}

File Handling
-------------


Readonly Fields, Permissions
----------------------------

Iktomi forms have a customizable permission layer. Two permissions supported by
default are read (`r`) and write (`w`).

Each field can have it's own permissions, but the common rule is that child
field permissions are subset of the parent field's (or form's) ones::

    class MyForm(Form):

        fields = [
            Field('name', permissions="rw")
        ]

    form = MyForm(permissions="r")

Permissions can be calculated dinamically based on environment (request, logged
in user roles, etc.).

Media Dependencies
------------------

For oldschool projects without js/css packing you can also use 
`iktomi.forms.media` layer to collect static files required for all form
widgets.

.. _form-copy:

Copy Interface
--------------

Some classes (fields, widgets, converters) implement copy by `__call__`. This is
very useful when making widely customizable interfaces.

You do not need to create a subclass every time you want reuse your widgets or
converters. From other side, there is no need to instantiate a class every time
with all the options.

Instead, you can just create an object once and then copy it redefining only
options you want::

    char = Char(length(0,100), NoUpper, required=False)

    field1 = Field(conv=conv)
    field2 = Field(conv=conv(required=True))

or even::

    field1 = Field(conv=Char(length(0, 100))
    field2 = field1(conv=field1.conv(required=True))
