.. _iktomi-web-tutorial:

Creating a simple app
=====================

Webob Request and Response objects are used.


Basic Practices
---------------

Hello, World
^^^^^^^^^^^^

Iktomi produces WSGI application from a couple of own web handlers.
In most cases, web handler is represented by function.

Here is the common interface of web handlers::

    def handler(env, data):
        ...
        return response

`env` is an iktomi application's current environment. Basically it 
contains only one significant attribute: `webob.Request` object in `env.request`.
`data` will be described below.

A handler returns `webob.Response`  or `None` (this case will be described below),
also it can raise `webob.exc.HTTPException` subclasses or call other 
(in most cases, next) handlers and return their result.

So, here is an example for very basic web handler::

    import webob

    def hello_world(env, data):
        name = env.request.GET.get('name', 'world')
        return webob.Response('Hello, %s!' %name)

Any handler can be converted to WSGI app::

    from iktomi import web
    from iktomi.web.app import Application

    wsgi_app = Application(hello_world)


Here it is! You can use the given object as common WSGI application, make server,
for example, using `Flup`. Implementation of development server can be found at
:ref:`Development server <iktomi-cli-app>`. Now we can create `manage.py` file with the 
following content::

    #!/usr/bin/python2.7
    import sys
    from iktomi.cli import manage
    from iktomi.cli.app import App
    
    def run():
        manage(dict(
            # dev-server
            app = App(wsgi_app),
        ), sys.argv)
    
    
    if __name__ == '__main__':
        run()


And now we can run the server::

    ./manage.py app:serve


Basic Routing
^^^^^^^^^^^^^

There are a couple of handlers to match different url parts or other request
properties: `web.match`, `web.prefix`, `web.methods`, `web.subdomain`, etc.

Iktomi routing is based on `web.cases` and `web.match` class. Constructor
of `web.cases` class accepts a couple of other handlers.
When called the `web.cases` instance calls 
each of handlers until one of them returns `webob.Response` object or 
raises `webob.exc.HTTPException`. 

If any handler returns `None`, it is interpreted as "request does not match, 
the handler has nothing to do with it and `web.cases` should try to call the next handler".

Constructor of `web.match` class accepts URL path to match and a handler name
to be used to build an URL (see below). If the request has been matched, `web.match` calls next handler,
otherwise returns `None`. Let's see an example::

    web.cases(
        web.match('/', 'index') | index,
        web.match('/contacts', 'contacts') | contacts,
        web.match('/about', 'about') | about,
    )

As we see, `|` operator chains handlers and makes second handler next for the first.

*Note: handlers are stateful, they store their next and nested handlers in the attributes.
Therefore, they can be reused (i.e. can be included in application in two places),
because `|` operator copies instances of handlers.*

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
if `contacts` handler returns `None`, `web.cases` does not stop iteration of handlers 
and `web.match('/about', 'about')` is called.

URL parameters
^^^^^^^^^^^^^^
If URL contains values that should be used in handlers (object ids, slugs, etc),
`werkzeug`-style URL parameters are used::

    web.match('/user/<int:user_id>')

Where `int` is name of an url converter, and `user_id` is attribute name.
All url-matching handlers use common url parsing engine.
They get parameters' values from url and put them to `data` object by `__setattr__`.

Iktomi provides some basic url converters: `string` (default), `int`, `bool`, `any`. 
It also allows you to create and use own ones (see below).

Nested handlers and URL Namespaces
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There is very handy way to logically organize your url map: namespaces::

    web.cases(
        web.prefix('/api', name="api") | web.cases(...),
        # this is equal to:
        # web.prefix('/api') | web.namespace('api') | web.cases(...),
        web.prefix('/user/<int:user_id>', name='user')  | web.cases(...),
    )

For more complex projects a simple combinations of `web.cases` and `web.match`
does not satisfy. Iktomi provides some handlers to create complex routing
rules and allows to create your own handlers. And you can combine handlers as you want. 
Here is an example::


    web.cases(
        web.prefix('/api', name="api") | web.methods(['GET']) | web.cases(
            web.match('/users', 'users') | users_list,
            web.match('/comments', 'comments') | comments_list
        ) | to_json,

        web.match('/', 'index') | index,
        web.prefix('/user/<int:user_id>', name="user") | web.cases(
            web.match('', 'profile') | user_profile,
            web.match('/comments', 'comments') | user_comments,
        )
    )

URL namespacing is useful to include similar app parts to many places
in your app, or for plug-in any reusable app from outside without warry 
about name clashes.::

    def handler(env, data):
        curr_namespace = env.namespace if hasattr(env, 'namespace') else None
        en_url = env.root.build_url('en.index')
        curr_url = env.root.build_url('.index')
        return webob.Response('%s %s %s' % (curr_namespace,
                                            en_url, curr_url))

    part = web.match('/index', 'index') | handler

    web.cases(
        # first renders "en /en/index /en/index"
        web.prefix('/en', name='en') | part,
        # second renders "ru /en/index /ru/index"
        web.prefix('/ru', name='ru') | part,
    )

Building URLs
^^^^^^^^^^^^^
Iktomi provides url building (or reversing) engine. 

URL reverse object is a callable that can be created for any handler::

    root = web.Reverse.from_handler(app)

or the same object can be found in `env.root` attribute during the request handling.

There are two ways of using `Reverse` object. Attribute-based one::

    root.user(user_id=5).as_url
    root.user(user_id=5).comments.as_url


or string-based method::

    root.build_url('user', user_id=5)
    root.build_url('user.comments', user_id=5)

*Note: string-based API is just a shortcut layer on top of attribute-based one*
*Note: attribute-based API returns a subreverse object (also `Reverse` instance),
while string-based API returns `web.URL` instances. If you want to get subreverse,
use `root.build_subreverse('user', user_id=5)`*

Controlling execution flow
^^^^^^^^^^^^^^^^^^^^^^^^^^
Iktomi allows to natively implement many use cases without any extra essences
like Django-middlewares, etc.

For example, to implement "middleware" you can do something like::

    @web.request_filter
    def wrapper(env, data, next_handler):
        do_something()
        result = next_handler(env, data)
        do_something_else(result)
        return result

    wrapped_app = wrapper | web.cases(..)

*Note: `web.request_filter` is decorator transforming function to regular WebHandler,
this allows to chain other handlers after given. The chained handler is passed as third
argument into the handler.*

It is transparent, obvious and native way. Also, it is possible to use try...except
statements with next_handler::

    @web.request_filter
    def wrapper(env, data, next_handler):
        try:
            return next_handler(env, data)
        except MyError:
            return exc.HTTPNotFound()

or even something like that::

    @web.request_filter
    def wrapper(env, data, next_handler):
        with open_db_connection() as db:
            env.db = db
            return next_handler(env, data)



Scopes of environment and data variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
`env` and `data` objects does not just store a data, also they 
delimitate data between handlers from differrent app parts. `web.cases` handler
is responsible for this delimitation. For each nested handler call it "stores"
the state of `env` and `data` objects and restores it after handler execution.

Each nested handler can change `env` and `data` objects and these changes will not affect 
other routing branches. So you don't worry about the data you've added
to `data` and `env` will involve any unexpected problems in other part of your app.
Therefore, be careful with this feature, it can lead to design mistakes.


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
Iktomi allows `webob.HTTPException` raising from inside a handler::

    from webob import exc

    @web.request_filter
    def handler(env, data, next_handler):
        if not is_allowed(env):
            raise exc.HTTPForbidden()
        return next_handler(env, data)

Also you can use `HTTPException` instances in route map::
    
    web.cases(
        web.match('/', 'index') | index,
        web.match('/contacts', 'contacts') | contacts,
        web.match('/about', 'about') | about,
        exc.HTTPNotFound(),
    )

Advanced Practices
------------------

Advanced routing tools
^^^^^^^^^^^^^^^^^^^^^^

Iktomi provides some additional filters.

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

A **static_files** handles static files requests and also provides a reverse function to build
urls for static files::

    static = web.static_files(cfg.STATIC_PATH, cfg.STATIC_URL)

    @web.request_filter
    def environment(env, data, next_handler):
        ...
        env.url_for_static = static.construct_reverse()
        ...

    app = web.request_filter(environment) | web.cases(
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


Make an application configurable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Configuring `env` object::

    class FrontEnvironment(web.AppEnvironment):
        cfg = cfg
        cache = memcache_client
    
        def __init__(self, *args, **kwargs):
            super(FrontEnvironment, self).__init__(*args, **kwargs)
            self.template_data = {}
    
        @cached_property
        def url_for(self):
            return self.root.build_url
    
        @storage_cached_property
        def template(storage):
            return BoundTemplate(storage, template_loader)
    
        @storage_method
        def render_to_string(storage, template_name, _data, *args, **kwargs):
            _data = dict(storage.template_data, **_data)
            result = storage.template.render(template_name, _data, *args, **kwargs)
            return Markup(result)
    
        @storage_method
        def render_to_response(self, template_name, _data,
                               content_type="text/html"):
            _data = dict(self.template_data, **_data)
            return self.template.render_to_response(template_name, _data,
                                                    content_type=content_type)
    
        @storage_method
        def redirect_to(storage, name, qs, **kwargs):
            url = storage.url_for(name, **kwargs)
            if qs:
                url = url.qs_set(qs)
            return HTTPSeeOther(location=str(url))
    
        def json(self, data):
            return webob.Response(json.dumps(data),
                                  content_type="application/json")
    
        @cached_property
        def db(self):
            return db_maker()
    
    wsgi_app = Application(app, env_class=FrontEnvironment)

Describe differences between `storage_method`, `storage_property`, `storage_cached_property`, 
`cached_property` here.


* `BoundTemplate` subclassing
* `environment` handler
