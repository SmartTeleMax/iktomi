.. _iktomi-web-advanced:


Advanced Practices
=====================

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
