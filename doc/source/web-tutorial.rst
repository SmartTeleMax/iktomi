.. _insanities-web-tutorial:

Creating a simple app
=====================

Webob Request and Response objects are used.


Basic Practices
---------------

Hello, World
^^^^^^^^^^^^

Insanities routing engine produces WSGI application from a couple of own web handlers.
In most cases, web handler is represented by function.

Here is the common interface of web handlers::

    def handler(env, data, next_handler):
        ...
        return response

`env` is an insanities application's current environment object. Basically it 
contains only one significant attribute: `webob.Request` object in `env.request`.
`data` and `next handler` will be described below.

A handler returns `webob.Response`  or `None` (this case will be described below).

So, here is an example for very basic web handler::

    import webob

    def hello_world(env, data, next_handler):
        name = env.request.GET.get('name', 'world')
        return webob.Response('Hello, %s!' %name)

This function can be converted to WebHandler object by `web.handler`
function. And any handler can be converted to WSGI app::

    from insanities import web

    wsgi_app = web.handler(hello_world).as_wsgi()

Here it is! You can use the given object as common WSGI application, make server,
for example, using `Flup`.


Basic Routing
^^^^^^^^^^^^^

Insanities provides some web handlers to ... 

Insanities routing is based on `web.cases` class. The constructor of this class 
accepts a couple of other headers and calls each of them until they return 
`webob.Response` object.

And there is a couple of handlers to match different url parts or other request
properties: `web.match`, `web.prefix`, `web.methods`, `web.subdomain`.


URL parameters
^^^^^^^^^^^^^^


Make an application configurable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bad title, it's about env.


Controlling execution flow
^^^^^^^^^^^^^^^^^^^^^^^^^^

Abuot various next_handler usecases


Scopes of environment and data valiables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Reversing URLs
^^^^^^^^^^^^^^


Smart URL object
^^^^^^^^^^^^^^^^


Throwing HTTPException
^^^^^^^^^^^^^^^^^^^^^^


Advanced Practices
------------------

Advanced routing tools
^^^^^^^^^^^^^^^^^^^^^^

subdomain, methods

Custom URL converters
^^^^^^^^^^^^^^^^^^^^^

URL Namespaces
^^^^^^^^^^^^^^



