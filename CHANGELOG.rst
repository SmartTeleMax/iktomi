4.1
---

* Correct path normalization for `static_files`.
* `ValidationError.format_args` added.
* `LaziCli` for lazy imports in manage.py file.

**Minor features**

* Regex can be set for url converters.
* Default error message `ValidationError` with no args.
* `webob.FileApp` is used for `static_files`.

**Minor Bugfixes**

* Fixed tests for HTML sanitizer
* Field.permissions still uses FieldPerm even if it is set by param
  Field(permisssions='rw')
* Fixed long-standing bug in routing: subdomains were not cleaned up from RouteState.
  RouteState is now immutable.
