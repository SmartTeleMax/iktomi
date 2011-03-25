# -*- coding: utf-8 -*-
'''
Module containing classes for easy and flexible HTML cleanup
'''

__all__ = ['Sanitizer', 'sanitize', 'remove_a_tags_without_href', 'strip_empty_tags',
           'strip_empty_tags_nested']

import re
from xml.sax.saxutils import escape, unescape
from html5lib import HTMLParser, sanitizer, treebuilders, treewalkers, serializer
from html5lib.constants import tokenTypes
from html5lib.html5parser import ParseError


SAFE_CLASSES = {}

class TokenSanitazer(sanitizer.HTMLSanitizer):

    escape_invalid_tags = False

    # only html (not SVG or MathML) elements and attributes
    allowed_elements = sanitizer.HTMLSanitizer.acceptable_elements
    allowed_attributes = sanitizer.HTMLSanitizer.acceptable_attributes
    allowed_classes = SAFE_CLASSES

    options = ('allowed_elements', 'allowed_attributes', 'allowed_css_properties',
               'allowed_css_keywords', 'allowed_protocols', 'escape_invalid_tags',
               'allowed_classes', 'attr_val_is_uri')

    def __init__(self, *args, **kwargs):
        for key in kwargs.keys():
            if key in self.options:
                setattr(self, key, kwargs.pop(key))
            elif key not in ('encoding', 'parseMeta', 'useChardet', 
                             'lowercaseElementName', 'lowercaseAttrName'):
                kwargs.pop(key)
        super(TokenSanitazer, self).__init__(*args, **kwargs)

    def sanitize_token(self, token):
        if token["type"] in (tokenTypes["StartTag"], tokenTypes["EndTag"], 
                             tokenTypes["EmptyTag"]):
            if token["name"] in self.allowed_elements:
                if token.has_key("data"):
                    # Copypasted from html5lib
                    attrs = dict([(name,val) for name,val in
                                  token["data"][::-1] 
                                  if name in self.allowed_attributes])
                    for attr in self.attr_val_is_uri:
                        if not attrs.has_key(attr):
                            continue
                        val_unescaped = re.sub("[`\000-\040\177-\240\s]+", '',
                                               unescape(attrs[attr])).lower()
                        #remove replacement characters from unescaped characters
                        val_unescaped = val_unescaped.replace(u"\ufffd", "")
                        if (re.match("^[a-z0-9][-+.a-z0-9]*:",val_unescaped) and
                            (val_unescaped.split(':')[0] not in 
                             self.allowed_protocols)):
                            del attrs[attr]
                    # end copypasted

                    if attrs.has_key('style'):
                        styles = self.sanitize_css(attrs.pop('style'))
                        if styles:
                            attrs['style'] = styles
                    if attrs.has_key('class'):
                        attrs = self.sanitize_classes(token, attrs)
                    token["data"] = [[name,val] for name,val in attrs.items()]
                return token
            elif self.escape_invalid_tags:
                return self.escape_token(token)
        elif token["type"] == tokenTypes["Comment"]:
            pass
        else:
            return token
        
    def sanitize_classes(self, token, attrs):
        # drop restricted classes
        classes = attrs.pop('class').split()
        if token['name'] in self.allowed_classes:
            allowed = self.allowed_classes[token['name']]
            condition = callable(allowed) and allowed or \
                        (lambda cls: cls in allowed)
            value = ' '.join(filter(condition, classes))
            if value:
                attrs['class'] = value
        return attrs
    
    def escape_token(self, token):
        # a part of html5lib sanitize_token method
        if token["type"] == tokenTypes["EndTag"]:
            token["data"] = "</%s>" % token["name"]
        elif token["data"]:
            attrs = ''.join([' %s="%s"' % (k,escape(v)) for k,v in token["data"]])
            token["data"] = "<%s%s>" % (token["name"],attrs)
        else:
            token["data"] = "<%s>" % token["name"]
        if token["type"] == tokenTypes["EmptyTag"]:
            token["data"] = token["data"][:-1] + "/>"
        token["type"] = tokenTypes["Characters"]
        del token["name"]
        return token

def remove_a_tags_without_href(dom_tree, **kwargs):
    a_tags = []
    for node in dom_tree.childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            if node.tagName == 'a':
                a_tags.append(node)
            a_tags.extend(node.getElementsByTagName('a'))
    a_tags = filter(lambda x: not x.hasAttribute('href'), a_tags)

    for a in a_tags:
        while a.childNodes:
            a.parentNode.insertBefore(a.childNodes[0],a)
        a.parentNode.removeChild(a)
        #a.unlink()
    return dom_tree


def strip_empty_tags(clean, drop_empty_tags=[], **kwargs):
    # XXX Sometimes doesn't work (with nested empty tags)
    for tag in drop_empty_tags:
        r = re.compile(r'<%s[^>]*>((\s|&nbsp;)*)<\/%s>' % (tag, tag), re.UNICODE)
        clean = r.sub(r'\1', clean)
    return clean

def strip_empty_tags_nested(clean, drop_empty_tags=[], **kwargs):
    # XXX Ugly but working function
    regs = [re.compile(r'<%s[^>]*>((\s|&nbsp;)*)<\/%s>' % (tag, tag), re.UNICODE)
            for tag in drop_empty_tags]
    subns = 1
    while subns:
        subns = 0
        for r in regs:
            clean, n = r.subn(r'\1', clean)
            subns += n
    return clean

class Sanitizer(object):
    '''
    Sanitizer object customizing sanitarization
    and providing method for sanitizing string.
    Is used by :class:`forms.convs.Html<insanities.forms.convs.Html>`.

    There are some options accepted by constructor:

    * *allowed_elements*. A list of HTML elements tag names
      that are not removed or escaped.
    * *allowed_attributes*. A list of HTML attributes that
      are not removed.
    * *escape_invalid_tags*. If it's True, disallowed HTML
      elements are escaped, otherwise they are removed.
    * *allowed_classes*. Dict with keys representing HTML
      tag names and values describing what classes are allowed
      for this element. It can be list of accepted classes
      (strings) or callable accepting the classname and
      returning condition if it is allowed::

        Sanitizer(allowed_classes={
            'p': ['hidden'],
            'span': re.compile('^num_\d+$').match,
        })
    * *strip_whitespaces*. Strip whitespaces or not.
    * *method*. Method of html rendering, default is xhtml.
      See html5lib docs for details.
    * *dom_callbacks*. A list of functions called after HTML
      is parsed. Function accept and returns minidom
      :class:`DocumentFragment` object and can process it. 
    * *string_callbacks*. A list of functions called after HTML
      is rendered. Function accept and returns the rendered
      HTML string. 

    For more options (including CSS, SVG, MathML cleanup)
    see source code and html5lib documentation.
    '''

    dom_callbacks = [remove_a_tags_without_href]
    string_callbacks = [strip_empty_tags]
    method = 'xhtml'
    strip_whitespace = True
    tokensanitazer = TokenSanitazer

    options = ('dom_callbacks', 'string_callbacks', 'method', 'strip_whitespace')

    def __init__(self, **kwargs):
        for key in kwargs.keys():
            if key in self.options:
                setattr(self, key, kwargs.pop(key))
        self.kwargs = kwargs

    def token_sanitizer(self):
        # Proxy function to pass arguments into Sanitizer constructor
        def func(*args, **kwargs):
            kwargs.update(self.kwargs)
            return self.tokensanitazer(*args, **kwargs)
        return func

    def get_dom(self, buf):
        buf = buf.strip()
        if not buf:
            return None
        p = HTMLParser(tree=treebuilders.getTreeBuilder("dom"),
                                tokenizer=self.token_sanitizer())
        return p.parseFragment(buf)

    def render(self, dom_tree):
        walker = treewalkers.getTreeWalker("dom")
        stream = walker(dom_tree)
        if self.method == "xhtml":
            Serializer = serializer.xhtmlserializer.XHTMLSerializer
        else:
            Serializer = serializer.htmlserializer.HTMLSerializer
        ser = Serializer(strip_whitespace=self.strip_whitespace,
                         quote_attr_values=True,
                         omit_optional_tags=False)
        return ser.render(stream)

    def sanitize(self, htmlstring):
        '''
        HTML sanitirization with html5lib-like interface
        '''
        dom_tree = self.get_dom(htmlstring)
        if dom_tree is None:
            return ''

        for callback in self.dom_callbacks:
            dom_tree = callback(dom_tree, **self.kwargs)

        clean = self.render(dom_tree)

        for callback in self.string_callbacks:
            clean = callback(clean, **self.kwargs)

        return unicode(clean)


def _get_list_props(cls):
    return [(opt, getattr(cls, opt))
            for opt in cls.options
            if type(getattr(cls, opt)) in (list, tuple)]


PROPERTIES = list(TokenSanitazer.options) + list(Sanitizer.options)
LIST_PROPERTIES = dict(_get_list_props(TokenSanitazer) + _get_list_props(Sanitizer))


def sanitize(buf, **kwargs):
    return Sanitizer(**kwargs).sanitize(buf)
