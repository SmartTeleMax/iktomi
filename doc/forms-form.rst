Form Class
==========

`iktomi.forms.form.Form` is the most top-level class in iktomi forms objects hierarchy.
Instances of this class encapsulate all the data needed to validate a form and
a result of the validation: :ref:`field<form-fields>` hierarchy with :ref:`converters<forms-convs>`
and :ref:`forms-widgets<widgets>`, initial data, raw data which is converted and validated, resulting
value, errors occured during validation, environment including all the data and
context related to current request.

Form instances are usually the only objects user interacts with on runtime
(during a request).

Form class is designed to serve on several purposes.

Form Validation
---------------

Form validation is done by `form.accept` method. This is main interface method of the form.

It accepts a `webob.MultiDict`-like object as argument and returns boolean value whether that value
passes validation or not. In particular, it can be `GET` and `POST` properties of `webob.Request`
object::

    form = MyForm()
    if form.accept(request.POST):
        do_something(form.python_data)

Forms are stateful, and `accept` method sets form state regarding given value. Here are some
variables representing form set:

* `form.is_valid`, a boolean value: wheter form validation was successful or not.
* `form.python_data`, a dictionary, result of form, actual converted value. Can be inconsistent if
  form is not valid.
* `form.raw_data` is a copy of input MultiDict possibly mutated in converting process. It contains
  all the values from all form's fields, but can also contain an unrelated values if they existed in
  the source MultiDict. To get canonical and clear raw value of the actual state of the form, use
  `Form.get_data` method.
* `form.errors` is a dictionary containing errors occured during validation. Key of the dict is
  field.input_name, and value is error message related to that field.

Rendering to HTML
-----------------

Form provide an interface to be rendered to HTML. This is `render` method. It takes no parameters
and renders a template with name equal to `form.template` passing form as a variable.

For example, if you have `form` variable in jinja2 template, you can call::

    <table>
        {{ form.render() }}
    </table>

In that template forms fields are iterated and each field is rendered by `field.widget.render()`.

If you have non-trivial HTML layout, it is OK to ignore `form.render` interface and call directly
`field.widget.render` method::

    {{ form.get_field('field_input_name').widget.render() }}

And finally, for sure, you can redefine a template name in your Form subclass::

    class MyForm(Form):

        template = "custom-form.html"
        fields = [...]

For details of rendering engine, see :ref:`Widgets<forms-widgets>` section.

Filling Initial Data
--------------------

Form may have initial value. This is useful, for example, for object editing
forms::

    initial = as_dict(obj)
    form = ObjForm(initial=obj)

Initial value is set to forms'python data, and then re-filled with each field's
loaded initial value. At the same time form's raw value is updated to be in
accordance with initial value.

To learn how each field loads an initial value, see :ref:`Fields: Setting
initial value<forms-fields-initial>` section.


Providing Access to the Environment
-----------------------------------

Form instances have one more purpose. They store `env` object, a request-level
iktomi environment, and provide an access to this environment for all other
objects in form hierarchy: fields, convs, widgets::

    form = MyForm(env)

    form.env # same as
    form.get_field(field_name).env # same as
    form.get_field(field_name).widget.env # same as
    form.get_field(field_name).conv.env

The environment can be used to acces a database, template engine, webob.Request,
configuration, etc.

.. About iktomi environment object see.
