Iktomi
==========

Iktomi is a python package providing some basic tools for creating web applications.
Iktomi is built on top of webob and supports Python 2.7.

It contains few independent subpackages, you can use both, or just one of them:

* **iktomi.web**, a flexible and extensible routing tool, suitable to dispatch HTTP
  requests between various views (or controllers). 
* **iktomi.forms**, a web forms validation and rendering tool.
* **iktomi.cli**, a layer for building command-line utilities.
* **iktomi.templates**, an adaptation layer for template engines, 
  in particular, for jinja2.
* **iktomi.db**, database utilities, in particular, sqlalchemy types, 
  collections, declarative mixins.

Some things are dedicated to package **iktomi.unstable**. This means the interfaces are 
unstable or unclear in some point, and we do not want to gurarantee their permanence 
for a long time.

Routing
-------

.. toctree::
    :maxdepth: 2

    web-basix
    web-advanced
    web-api

Forms
-----

.. toctree::
    :maxdepth: 1

    forms-basic
    forms-api

Cli
---

.. toctree::
    :maxdepth: 2

    cli-app
    cli-fcgi
    cli-sqla
    cli-api

Utilities
---------

Unsorted stuff for make iktomi working.

.. toctree::
    :maxdepth: 2

    utils

