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

Rendering to HTML
-----------------

Filling Initial Data
--------------------

Storing Raw and Python Data
---------------------------

Providing Access to the Environment
-----------------------------------
