Widgets
=======

`iktomi.forms.widget.Widget` instances are responsible for visual representation
of an item.

Widgets implement :ref:`copy<form-copy>` interface.

Rendering
---------

General way to render a form to HTML is to call `Form.render` method. This method
iterates over all top-level fields and calls their widgets' `render` methods. This 
method is called to get HTML code of field with actual value.

Widget can do some data preparations and finally it is rendered to template
named `widget.template` (by default, `jinja2` is used).
You can redefine  template name by passing it to the widget::

    class MyWidget(TextInput):

        template = 'widgets/my-widget.html'

    widget = MyWidget(template="widgets/my-widget-2.html")

Widget class is considered to render a widget itself, without labels, hints, 
form layout, etc. These things are rendered in parent instance 
(form or parent field's widget)

Render Types
------------

As we just have learned above, widget labels, form layout, etc are rendered 
in parent template. But there is some inconsistense, because different widgets
can expect different different layout. For example, checkboxes usually 
should be rendered on the left to the label, while ordinary field's widget 
should be on the right.

Iktomi provides a way to make this trick. There is a widget attribute called 
`render_type`, parent instance can use it to figure out how to render the widget,
the implementation of expected layout is completely on parent instance::

    widget = MyWidget(render_type="full-width")

There are a few render types supported by default, and you are free to implement 
own one:

* `'default'`: label is rendered in usual place;
* `'checkbox'`: label and widget are rendered close to each other;
* `'full-width'`: for table-like templates, a widget takes a full row of the form,
  the label can be rendered above the widget;
* `'hidden'`: label is not rendered, and the widget is rendered in hidden HTML
  element.

Data Preparations
-----------------

If you need to pass extra data to template, you can extend `Widget.prepare_data`
method::

    class MyWidget(TextInput):
        def prepare_data(self):
            template_data = TextInput.prepare_data(self)
            value = template_data['value']
            var1 = get_var1(value)
            return dict(template_data,
                        var1=var1)

Multiple and Redonly options
----------------------------

The important thing, widget implementation should carry about, is to support
`readonly` option, and, optionally, support `multiple` option.

Readonly fields can not be changed by user, and it should be represented in user 
interface. For example, `<select readonly="readonly">` or 
`<input disabled="disabled">` can be used. It is recommended to still submit
readonly widget's value, so duplicating disabled input (which is not submitted) 
with hidden input containing actual value is fine.

Multiple options indicate that the field has `conv.ListOf` instance as it's converter.
Fields of this kind accept multiple values under the same name. From HTML 
point of view it can be implemented, for example, as 
`<select multiple="multiple">` or as multiple checkboxes with the same name.

.. Rendering Aggregate Fields
.. --------------------------

Widget implementations
----------------------

Examples of widgets are `TextInput`, `Textarea`, `Select`, `CheckBox`, 
`HiddenInput`, etc.

