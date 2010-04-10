# -*- coding: utf-8 -*-

__all__ = ['match', 'method', 'static']

import logging
import re
import httplib
from os import path
from urllib import quote, unquote
from .core import RequestHandler, ContinueRoute
from .urlconvs import ConvertError
from .http import RequestContext, HttpException
from .urlconvs import convs_dict


logger = logging.getLogger(__name__)


class match(RequestHandler):

    _split_pattern = re.compile(r'(<[^<]*>)')
    _converter_pattern = re.compile(r'''^<
            (?P<converter>[a-zA-Z_][a-zA-Z0-9]+)    # converter name
            (?P<args>\(.*?\))?                      # converter args
            \:?                                     # delimiter
            (?P<variable>[a-zA-Z_][a-zA-Z0-9_]+)?    # variable name
            >$''', re.VERBOSE)
    _static_url_pattern = re.compile(r'^[^<]*?$')

    def __init__(self, url, name, converters=None):
        super(match,self).__init__()
        self.url = url
        self.url_name = name
        self._allowed_converters = self._init_converters(converters)
        self._builder_params = []
        self._converters = {}
        self._pattern = re.compile(self._parse(url))

    def trace(self, tracer):
        tracer.url_name(self.url_name)
        tracer.builder(self.build)

    def handle(self, rctx):
        m = self._pattern.match(unquote(rctx.request.path))
        if m:
            logger.debug('match - Got match for url "%s"' % rctx.request.path)
            kwargs = m.groupdict()
            # convert params
            for k,v in kwargs.items():
                conv_name, args = self._converters[k]
                # now we replace converter by class instance
                conv = self._init_converter(conv_name, args)
                try:
                    kwargs[k] = conv.to_python(v)
                except ConvertError:
                    logger.debug('ConverterError by "%s", value "%s"' % (k, v.encode('utf-8')))
                    raise ContinueRoute(self)
            if kwargs:
                rctx.template_data.update(kwargs)
            rctx.response.status = httplib.OK
            return rctx
        raise ContinueRoute(self)

    def _parse(self, url):
        result = r'^'
        parts = self._split_pattern.split(url)
        total_parts = len(parts)
        for i, part in enumerate(parts):
            if part:
                is_url_pattern = self._static_url_pattern.match(part)
                if is_url_pattern:
                    result += re.escape(part)
                    self._builder_params.append(part)
                    continue
                is_converter = self._converter_pattern.match(part)
                if is_converter:
                    converter = is_converter.groupdict()['converter']
                    args = is_converter.groupdict()['args']
                    variable = is_converter.groupdict()['variable']
                    if variable is None:
                        variable = converter
                        converter = 'string'
                    result += '(?P<%s>[a-zA-Z0-9_%%-]+)' % variable
                    self._builder_params.append([variable, converter, args])
                    self._converters[variable] = [converter, args]
                    continue
                raise ValueError('Incorrect url "%s"' % url)
            else:
                if i < total_parts - 1:
                    raise ValueError('Incorrect url "%s"' % url)
        result += '$'
        return result

    def build(self, prefixes=None, **kwargs):
        prefixes = prefixes and prefixes or []
        prefix = ''.join(prefixes)
        result = ''
        for part in self._builder_params:
            if isinstance(part, list):
                var, conv_name, args = part
                conv = self._init_converter(conv_name, args)
                value = kwargs[var]
                result += conv.to_url(value)
            else:
                result += part
        return prefix + result

    def _init_converter(self, conv_name, args):
        try:
            conv = self._allowed_converters[conv_name]
        except KeyError:
            raise KeyError('There is no converter named "%s"' % conv_name)
        else:
            if args:
                conv = conv()
            else:
                conv = conv()
        return conv

    def _init_converters(self, converters):
        convs = convs_dict.copy()
        if converters is not None:
            for conv in converters:
                 name = conv.name or conv.__name__
                 convs[name] = conv
        return convs

    def __repr__(self):
        return '%s(\'%s\', \'%s\')' % \
                (self.__class__.__name__, self.url, self.url_name)


class method(RequestHandler):

    def __init__(self, *names):
        super(method, self).__init__()
        self._names = [name.upper() for name in names]

    def handle(self, rctx):
        if rctx.request.method in self._names:
            return rctx
        raise ContinueRoute(self)

    def __repr__(self):
        return 'method(*%r)' % self._names


class static(RequestHandler):

    def __init__(self, prefix, path):
        super(static, self).__init__()
        self.prefix = prefix
        self.path = path

    def handle(self, rctx):
        def url_for_static(part):
            return path.join(self.prefix, part)

        rctx.template_data['url_for_static'] = url_for_static

        if rctx.request.path.startswith(self.prefix):
            static_path = rctx.request.path[len(self.prefix):]
            file_path = path.join(self.path, static_path)
            if path.exists(file_path) and path.isfile(file_path):
                rctx.response.status = httplib.OK
                file = open(file_path, 'r')
                rctx.response.write(file.read())
                file.close()
                return rctx
            else:
                raise HttpException(404)
        raise ContinueRoute(self)
