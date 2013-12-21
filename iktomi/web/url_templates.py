# -*- coding: utf-8 -*-

import urllib
import re
import logging
from .url_converters import default_converters, ConvertError

logger = logging.getLogger(__name__)


def urlquote(value):
    return urllib.quote(value.encode('utf-8') if isinstance(value, unicode) else str(value))


class UrlBuildingError(Exception): pass


_split_pattern = re.compile(r'(<[^<]*>)')

#NOTE: taken from werkzeug
_converter_pattern = re.compile(r'''^<
        (?:
            (?P<converter>[a-zA-Z_][a-zA-Z0-9_]+)   # converter name
            (?:\((?P<args>.*?)\))?                  # converter args
            \:                                      # delimiter
        )?
        (?P<variable>[a-zA-Z_][a-zA-Z0-9_]*)        # variable name
        >$''', re.VERBOSE | re.U)

_static_url_pattern = re.compile(r'^[^<]*?$')

def construct_re(url_template, match_whole_str=False, converters=None,
                 default_converter='string'):
    '''
    url_template - str or unicode representing template

    Constructed pattern expects urlencoded string!

    returns  (compiled re pattern, 
              dict {url param name: [converter name, converter args (str)]},
              list of (variable name, converter name, converter args name))
    '''
    # needed for reverse url building (or not needed?)
    builder_params = []
    # found url params and their converters
    url_params = {}
    result = r'^'
    parts = _split_pattern.split(url_template)
    for i, part in enumerate(parts):
        is_url_pattern = _static_url_pattern.match(part)
        if is_url_pattern:
            #NOTE: right order:
            #      - make part str if it was unicode
            #      - urlquote part
            #      - escape all specific for re chars in part
            part = urlquote(unicode(part).encode('utf-8'))
            result += re.escape(part)
            builder_params.append(part)
            continue
        is_converter = _converter_pattern.match(part)
        if is_converter:
            groups = is_converter.groupdict()
            converter_name = groups['converter'] or default_converter
            conv_object = init_converter(converters[converter_name],
                                         groups['args'])
            variable = groups['variable']
            builder_params.append((variable, conv_object))
            url_params[variable] = conv_object
            result += '(?P<%s>%s)' % (variable, conv_object.regex)
            continue
        raise ValueError('Incorrect url template "%s"' % url_template)
    if match_whole_str:
        result += '$'
    return re.compile(result), url_params, builder_params


def init_converter(conv_class, args):
    if args:
        #XXX: taken from werkzeug
        storage = type('_Storage', (), {'__getitem__': lambda s, x: x})()
        args, kwargs = eval(u'(lambda *a, **kw: (a, kw))(%s)' % args, {}, storage)
        return conv_class(*args, **kwargs)
    return conv_class()


class UrlTemplate(object):

    def __init__(self, template, match_whole_str=True, converters=None,
                 default_converter='string'):
        self.template = template
        self.match_whole_str = match_whole_str
        self._allowed_converters = self._init_converters(converters)
        self._pattern, self._url_params, self._builder_params = \
            construct_re(template,
                         match_whole_str=match_whole_str,
                         converters=self._allowed_converters,
                         default_converter=default_converter)

    def match(self, path, **kw):
        '''
        path - str (urlencoded)
        '''
        m = self._pattern.match(path)
        if m:
            kwargs = m.groupdict()
            # convert params
            for url_arg_name, value_urlencoded in kwargs.items():
                conv_obj = self._url_params[url_arg_name]
                unicode_value = urllib.unquote(value_urlencoded).decode('utf-8', 'replace')
                try:
                    kwargs[url_arg_name] = conv_obj.to_python(unicode_value, **kw)
                except ConvertError, err:
                    logger.debug('ConvertError in parameter "%s" '
                                 'by %r, value "%s"',
                                 url_arg_name,
                                 err.converter.__class__,
                                 err.value)
                    return None, {}
            return m.group(), kwargs
        return None, {}

    def __call__(self, **kwargs):
        'Url building with url params values taken from kwargs. (reverse)'
        result = ''
        for part in self._builder_params:
            if isinstance(part, tuple):
                var, conv_obj = part
                try:
                    value = kwargs[var]
                except KeyError:
                    if conv_obj.default is not conv_obj.NotSet:
                        value = conv_obj.default
                    else:
                        raise UrlBuildingError('Missing argument for '
                                               'URL builder: %s' % var)
                result += urlquote(conv_obj.to_url(value))
            else:
                result += part
        # result - urlencoded str
        return result

    def _init_converters(self, converters):
        convs = default_converters.copy()
        if converters is not None:
            convs.update(converters)
        return convs

    def __eq__(self, other):
        return self.template == other.template and \
               self.match_whole_str == other.match_whole_str

    def __repr__(self):
        return '%s(%r, match_whole_str=%r)' % (self.__class__.__name__, 
                                               self.template.encode('utf-8'),
                                               self.match_whole_str)
