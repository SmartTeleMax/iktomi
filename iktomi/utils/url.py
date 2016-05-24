# -*- coding: utf-8 -*-
"""
    Originally from werkzeug.urls

    :copyright: (c) 2014 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD
"""
from six import text_type
from six.moves.urllib.parse import quote

_hexdigits = '0123456789ABCDEFabcdef'
_hextobyte = dict(
    ((a + b).encode(), int(a + b, 16))
    for a in _hexdigits for b in _hexdigits
)

def url_unquote(string, unsafe=''):
    """URL decode a single string with a given encoding.  If the charset
    is set to `None` no unicode decoding is performed and raw bytes
    are returned.

    :param string: the string to unquote.
    """
    rv = _unquote_to_bytes(string, unsafe)
    return repercent_broken_unicode(rv)


def _unquote_to_bytes(string, unsafe=''):
    if isinstance(string, text_type):
        string = string.encode('utf-8')
    if isinstance(unsafe, text_type):
        unsafe = unsafe.encode('utf-8')
    unsafe = frozenset(bytearray(unsafe))
    bits = iter(string.split(b'%'))
    result = bytearray(next(bits, b''))
    for item in bits:
        try:
            char = _hextobyte[item[:2]]
            if char in unsafe:
                raise KeyError()
            result.append(char)
            result.extend(item[2:])
        except KeyError:
            result.extend(b'%')
            result.extend(item)
    return bytes(result)


def repercent_broken_unicode(path):
    """
    As per section 3.2 of RFC 3987, step three of converting a URI into an IRI,
    we need to re-percent-encode any octet produced that is not part of a
    strictly legal UTF-8 octet sequence.
    """
    # originally from django.utils.encoding
    while True:
        try:
            return path.decode('utf-8')
        except UnicodeDecodeError as e:
            repercent = quote(path[e.start:e.end], safe=b"/#%[]=:;$&()+,!?*@'~")
            path = path[:e.start] + repercent.encode('ascii') + path[e.end:]


def uri_to_iri_parts(path, query, fragment):
    r"""
    Converts a URI parts to corresponding IRI parts in a given charset.

    Examples for URI versus IRI:

    :param path: The path of URI to convert.
    :param query: The query string of URI to convert.
    :param fragment: The fragment of URI to convert.
    """
    path = url_unquote(path, '%/;?')
    query = url_unquote(query, '%;/?:@&=+,$#')
    fragment = url_unquote(fragment, '%;/?:@&=+,$#')
    return path, query, fragment

