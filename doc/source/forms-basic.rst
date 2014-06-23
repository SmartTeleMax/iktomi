.. _iktomi-forms-basic:

Form abstraction layers
=======================

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
^^^^^

`iktomi.forms.form.Form` subclasses contain a scheme of validated data as list
of fields. Instances of these classes provide an interface to work with entire
form, such as: validate the data (`Form.accept`), render the entire form
(`Form.render`). Also they store common form data: initial, raw and resulting
values, environment, errors occured during validation.

Fields
^^^^^^

`iktomi.forms.fields.BaseField` instances represent one node in data scheme.
It can be atomic data (string, integer, boolean) or data aggregated from
collection of other fields (`FieldList` or `FieldSet`, see below).

Each field has a name. Name is a key in resulting value dictionary.

Also there are a few auxillary attributes like `label`, `hint`.

Finally, the main options of `BaseField` instances are converter and widget
objects.

Converters
^^^^^^^^^

`iktomi.forms.convs.Converter` instances are responsible for all staff related
to data validation and convertation. Converters provide  methods for
transformations in two directions:

* `to_python`
* `from_python`

Examples of converters are `Int`, `Char`, `Html`, `Date`.

Widgets
^^^^^^^

`iktomi.forms.widget.Widget` instances are responsible for visual representation
of an item.

The main method of widget is `render`, which is called to get HTML code of field
with actual value.


Aggregate fields
^^^^^^^^^^^^^^^^

Readonly fields, permissions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Also there is a permission layer

Media dependencies
^^^^^^^^^^^^^^^^^^
For oldschool projects without js/css packing you can also use 
`iktomi.forms.media` layer to collect static files required for all form
widgets.

