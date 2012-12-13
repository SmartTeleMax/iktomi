.. _iktomi-web-tutorial:

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

`env` is an iktomi application's current environment object. Basically it 
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

    from iktomi import web

    wsgi_app = web.handler(hello_world).as_wsgi()

Here it is! You can use the given object as common WSGI application, make server,
for example, using `Flup`.


Basic Routing
^^^^^^^^^^^^^

There is a couple of handlers to match different url parts or other request
properties: `web.match`, `web.prefix`, `web.methods`, `web.subdomain`, etc.

Insanities routing is based on `web.cases` and `web.match` class. Constructor 
of class accepts a couple of other handlers. When called the instance calls 
each of handlers until it returns `webob.Response` object. 

Constructor of `web.match` class accepts a URL path to match and a handler name
to be used for url building (see below). When called it calls next handler only
for requests with matching urls. Let's see an example::

    web.cases(
        web.match('/', 'index') | index,
        web.match('/contacts', 'contacts') | contacts,
        web.match('/about', 'about') | about,
    )

As we see, `|` operator chains handlers and makes second handler next for first.
Important: handlers are not reusable, i.e. can't be included in application in two places.

And here's how it works. For request::

    GET /contacts

1. `web.cases` is called, it calls the first `web.match` handler
2. `web.match('/', 'index')` does not accept the request and returns None.
3. `web.cases` gets `None` from first handler and calls the next.
4. `web.match('/contacts', 'contacts')` accepts the request, calls next 
   handler (contacts) and returns it's result.
5. `web.cases` gets not-None result from handler, stops iteration over
   handlers and returns the result.

Note that execution of chain can be cancelled by every handler. For example, 
if `contacts` returns None, `web.cases` does not stop iteration of handlers 
and `web.match('/about', 'about')` is called.

URL parameters
^^^^^^^^^^^^^^
If URL contains data that should be used in heandlers (object ids, slugs, ets),
`werkzeug`-style URL parameters can be used in `web.match` and `web.prefix` handlers::

    web.match('/user/<int:user_id>')

These handlers use common url parsing engine. They get parameters' values from url and
put them to `data` object by `__setattr__`.

Insanities provides some basic url converterss: `string` (default), `int`, `bool`, `any`. 
It also allows you to create and use own ones (see below).

Nested handlers
^^^^^^^^^^^^^^^
For more complex projects a simple combinations of `web.cases` and `web.match`
does not satisfy. Insanities provides some handlers to create complex routing
rules and allows to create your own handlers. And you can combine handlers as you want. 
Here is an example::

    web.cases(
        web.prefix('/api') | web.methods(['GET']) | web.cases(
            web.match('/users', 'api_users') | users_list,
            web.match('/comments', 'api_comments') | comments_list
        ) | to_json,

        web.match('/', 'index') | index,
        web.prefix('user/<int:user_id>') | web.cases(
            web.match('', 'user_profile') | user_profile,
            web.match('/comments', 'user_comments') | user_comments,
        )
    )

Building URLs
^^^^^^^^^^^^^
Insanities provides url building (or reversing) engine. 

URL reverse object is a callable that can be created for any handler::

    url_for = web.Reverse(web.locations(app))

And this function can be used anywhere::
    
    url_for('user', user_id=5)

Controlling execution flow
^^^^^^^^^^^^^^^^^^^^^^^^^^
Insanities allows to natively implement many use cases without any extra essences
like Django-middlewares, etc.

For example, to implement "middleware" you can do something like::

    def wrapper(env, data, next_handler):
        do_something()
        result = next_handler(env, data)
        do_something_else(result)
        return result

    wrapped_app = web.handler(wrapper) | app

It is transparent, obvious and native way. Also, it is possible to use try...except
statements with next_handler::

    def wrapper(env, data, next_handler):
        try:
            return next_handler(env, data)
        except MyError:
            return exc.HTTPNotFound()

Make an application configurable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Common way to apply configuration and plug-in any engines is to define configuration 
function that puts all config parameters into `env` and chain it before app.
For example::

    import cfg
    from iktomi import web
    from iktomi.templates import jinja2, Template

    template = Template(cfg.TEMPLATES, jinja2.TEMPLATE_DIR,
                        engines={'html': jinja2.TemplateEngine})

    def environment(env, data, next_handler):
        env.cfg = cfg

        env.url_for = url_for
        env.template = template
        env.db = my_db_engine()
        env.cache = memcache_client

        try:
            return next_handler(env, data)
        finally:
            env.db.close()

    app = web.handler(environment) | app

    url_for = web.Reverse(web.locations(app))

About `iktomi.template` see in :ref:`corresponding docs <iktomi-templates>`.

Scopes of environment and data valiables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
`env` and `data` objects does not just store a data, they are also used for
delimitate data between handlers from differrent app parts. `web.cases` handler
is responsible for this delimitation. When called it stores it's inittial 
state before calling nested handlers.

Each nested handler can change `env` and `data` objects. If the handler finishes 
successfully, `web.cases` accepts  changes, otherwise it rolls changes back 
and calls next nested handler::

    example is needed

So you don't worry about the data you've added to `data` and `env` will involve
any unexpected problems in other part of your app.

Smart URL object
^^^^^^^^^^^^^^^^
URL build functions does not return actually `str` object, but it's `web.URL`
subclass'es instance. It allows to make common operations with queryString
parameters (add, set, delete) and also has method returning
URL as human-readable unicode string::

    >>> print(URL('/').set(q=1))
    /?q=1
    >>> print(URL('/').set(q=1).add(q=2))
    /?q=1&q=2
    >>> print(URL('/').set(q=1).set(q=3))
    /?q=3
    >>> print(URL('/').set(q=1).delete('q'))
    /
    >>> print(URL('/', host=u"образец.рф").set(q=u'ок'))
    http://xn--80abnh6an9b.xn--p1ai/?q=%D0%BE%D0%BA
    >>> print(URL('/', host=u"образец.рф").set(q=u'ок').get_readable())
    http://образец.рф/?q=ок

Throwing HTTPException
^^^^^^^^^^^^^^^^^^^^^^
Insanities uses webob HTTP exceptions::

    from webob import exc

    def handler(env, data, next_handler):
        if not is_allowed(env):
            raise exc.HTTPForbidden()
        return next_handler(env, data)

Advanced Practices
------------------

Advanced routing tools
^^^^^^^^^^^^^^^^^^^^^^

Insanities provides some additional filters.

A **subdomain** filter allows to select requests with a given domain or subdomain::

    web.cases(
        web.subdomain('example.com') | web.cases(
            web.match('/', 'index1') | index1,
        ),
        web.subdomain('example.org') | web.cases(
            web.match('/', 'index2') | index2,
        ),
    )

You can use multiple subdomain filters in a line to select lower-level subdomains.
To specify a base domain chain one subdomain filter before::
    
    web.subdomain('example.com') | web.cases(
        # all *.example.com requests get here
        web.subdomain('my') | web.cases(
            # all *.my.example.com requests get here
            ...
        ),
        ...
    )

A **ctype** filters allows to select requests with specified Content-Type HTTP header.
You can also use shortcuts for most common content types (*xml*, *json*, *html*, *xhtml*)::

    web.cases(
        ctype('text/html') | web.cases(
            # only html requests get here
            ...
        ),
        ctype(ctype.xml, ctype.json) | web.cases(
            # only xml or json requests get here
            ...
        ),
    )

A **static_files** handles static files requests and also provides a reverse function to build
urls for static files::

    static = web.static_files(cfg.STATIC_PATH, cfg.STATIC_URL)

    def environment(env, data, next_handler):
        ...
        env.url_for_static = static.construct_reverse()
        ...

    app = web.handler(environment) | web.cases(
        static,
        ...
    )

.. Check this text

Handling files is provided for development and testing reasons. You can use it to serve static
file on development server, but it is strictly not recommended to use it for this purpose on
production (use your web server configuration requests instead of it). Surely, reverse function
is recommended to use on both production and development servers.


Custom URL converters
^^^^^^^^^^^^^^^^^^^^^
You can add custom URL converters by subclassing `web.url.Converter`.
A subclass should provide `to_python` and `to_url` methods. First accepts **unicode**
url part and returns any python object. Second does reverse transformation. Note, that
url parts are escaped automatically outside URL converter::

    class MonthConv(url.Converter):
        def to_python(self, value, **kwargs):
            try:
                return int(value)
            except ValueError:
                raise ConvertError(self.name, value)

        def to_url(self, value):
            return str(value)

To include URL converter, pass `convs` argument to handler constructor::

    prefix('/<month:month_num>', convs={'month': MonthConv})


URL Namespaces
^^^^^^^^^^^^^^

URL namespacing is useful to include similar app parts to many places
in your app, or for plug-in any reusable app from outside without warry 
about name clashes.::

    def part():
        def handler(env, data, next_handler):
            curr_namespace = env.namespace if 'namespace' in env else None
            en_url = env.url_for('en.index')
            curr_url = env.url_for('.index')
            return webob.Response('%s %s %s' % (curr_namespace,
                                                en_url, curr_url))

        return web.cases(
            web.match('/index', 'index') | handler,
        )

    web.cases(
        # first renders "en /en/index /en/index"
        web.prefix('/en') | web.namespace('en') | part(),
        # second renders "ru /en/index /ru/index"
        web.prefix('/ru') | web.namespace('ru') | part(),
    )

