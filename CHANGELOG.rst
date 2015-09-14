0.4.2
-----

* Option for Html cleaner: wrap inline tags in paragraphs on the top level.
* Fixed schema generation whith dialect-specific fields.
* Fixed schema generation for single DB configuration.
* SQLAlchemy 1.0 support; drop support of SQLAlchemy 0.8.


**Minor features:**

* Save url template in prefix, so it can be accessed.
* JS-compatible URL template regexp compilation option: allows to dump
  URL maps to JSON.
* Informative exception when metadata is not defined in model module in 
  multi-DB configuration.
* ResizeCrop accept force option: image will be cropped to target 
  proportion even it is smaller that target size.
* Command-line autocompletion interface.
* Made Html converter's tag wrapping behaviour configurable
* Html Cleaner ability to drop empty tags (configurable).
* ImageResizer's interface change: pass size instead of image object, making it useful
  in AJAX requests handling.
* Add option `rate` to ResizeMixed, determining at which rate the image is 
  considered vertical or horizontal.
* Redefinable `file_manager` for `FileFieldSetConv`.
* Used `base64` to generate random file names for both transient and persistent files.
* Allow to set a length for both persistent and transient random file names.
* `find_file_manager` now accepts mapped objects with metadata.
* Added create_symlink method to `FileManager`.
* Support multiple arguments for `URL.qs_delete`.

**Minor bugfixes:**

* Fixed image resizer failing in some cases.
* Fixed cache_properties when setting PersistentFile to file attribute
* Warning instead of exception during image resizing via fill_from property
  if original file has been lost.
* URL.from_url does not fail for broken unicode input.
* Fixed error handling and non-response return object in application.
* Fixed drop table command if there are no tables in metadata.
* Fixed readonly FieldBlock.
* Fixed PublicQuery.with_entities() to honor public condition.
* Fixed the case there is no logfile passed to fcgi CLI command.
* Fixed `None` python value handling in `convs.List.from_python`.
* Return 404 if static directory is requested.

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
