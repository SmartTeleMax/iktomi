0.4.2
-----

* Option for Html cleaner: wrap inline tags in paragraphs on the top level.
* Fixed schema generation whith dialect-specific fields.

**Minor features:**

* Save url template in prefix, so it can be accessed.
* JS-compatible URL template regexp compilation option: allows to dump
  URL maps to JSON.
* Informative exception when metadata is not defined in model module in 
  multi-DB configuration.
* ResizeCrop accept force option: image will be cropped to target 
  proportion even it is smaller that target size.

**Minor bugfixes:**

* Fixed image resizer failing in some cases.
* Fixed cache_properties when setting PersistentFile to file attribute
* Warning instead of exception during image resizing via fill_from property
  if original file has been lost.
* URL.from_url does not fail for broken unicode input.

0.4.1
-----

* Correct path normalization for `static_files`.
* `ValidationError.format_args` added.
* `LaziCli` for lazy imports in manage.py file.

**Minor features:**

* Regex can be set for url converters.
* Default error message `ValidationError` with no args.
* `webob.FileApp` is used for `static_files`.

**Minor bugfixes:**

* Fixed tests for HTML sanitizer
* Field.permissions still uses FieldPerm even if it is set by param
  Field(permisssions='rw')
* Fixed long-standing bug in routing: subdomains were not cleaned up from RouteState.
  RouteState is now immutable.
