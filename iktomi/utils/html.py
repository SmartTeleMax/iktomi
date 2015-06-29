# -*- coding: utf-8 -*-

from urlparse import urlsplit
from lxml import html
from lxml.html import clean
# XXX move to iktomi.cms?

class Cleaner(clean.Cleaner):

    safe_attrs_only = True
    remove_unknown_tags = None
    drop_empty_tags = frozenset()
    dom_callbacks = []
    allow_external_src = False
    allowed_protocols = frozenset(['http', 'https', 'mailto'])
    # None to allow all classes
    allow_classes = {}
    attr_val_is_uri = ['href', 'src', 'cite', 'action', 'longdesc']
    a_without_href = True
    # False : no tags wrapping;
    # None : try to wrap tags on top in 'p' if 'p' is allowed or 'div'
    # True : try to wrap tags on top in 'p' if 'p' is allowed or 'div', 
    #    and raise error if no get_wrapper_tag was found
    # if div allowed;
    # 'div'/'p' : wrap tags in 'div' or 'p' respectively
    # lambda : wrap tags in tag from lambda
    wrap_inline_tags = None
    # Tags to wrap in paragraphs on top
    tags_to_wrap = ['b', 'big', 'i', 'small', 'tt',
                    'abbr', 'acronym', 'cite', 'code',
                    'dfn', 'em', 'kbd', 'strong', 'samp',
                    'var', 'a', 'bdo', 'br', 'map', 'object',
                    'q', 'span', 'sub', 'sup']

    def __init__(self, *args, **kwargs):
        clean.Cleaner.__init__(self, *args, **kwargs)
        if self.wrap_inline_tags is True:
            if self.get_wrapper_tag() is None:
                raise ValueError('Cannot find top element')

    def __call__(self, doc):
        clean.Cleaner.__call__(self, doc)
        if hasattr(doc, 'getroot'):
            # ElementTree instance, instead of an element
            doc = doc.getroot()
        self.extra_clean(doc)

    # retrieve tag to wrap around inline tags
    def get_wrapper_tag(self):
        if self.allow_tags is None:
            return
        if self.wrap_inline_tags in (None, True):
            if 'p' in self.allow_tags:
                return html.Element('p')
            elif 'div' in self.allow_tags:
                return html.Element('div')
        elif self.wrap_inline_tags in ('p', 'div'):
            if 'p' in self.allow_tags or 'div' in self.allow_tags:
                return html.Element(self.wrap_inline_tags)
        elif callable(self.wrap_inline_tags):
            element = self.wrap_inline_tags()
            if element.tag in self.allow_tags:
                return element

    def clean_top(self, doc):
        par = None
        first_par = False
        if self.get_wrapper_tag() is None:
            return
        # create paragraph if there text in the beginning of top
        if (doc.text or "").strip():
            par = self.get_wrapper_tag()
            doc.insert(0, par)
            par.text = doc.text
            doc.text = None
            # remember if first paragraph created from text
            first_par = True

        for child in doc.getchildren():
            i = doc.index(child)

            if child.tag == 'br' and 'br' in self.tags_to_wrap:
                if (child.tail or "").strip():
                    par = self.get_wrapper_tag()
                    doc.insert(i, par)
                    par.text = child.tail
                doc.remove(child)
                continue

            if child.tag not in self.tags_to_wrap and \
                    (child.tail or "").strip():
                par = self.get_wrapper_tag()
                par.text = child.tail
                child.tail = None
                doc.insert(i+1, par)
                continue

            if child.tag in self.tags_to_wrap:
                if par is None:
                    par = self.get_wrapper_tag()
                    doc.insert(i, par)
                par.append(child)
            else:
                if first_par and i == 0:
                    continue
                par = None

    def is_element_empty(self, el):
        if el.tag == 'br':
            return True
        if el.tag not in self.drop_empty_tags:
            return False
        children = el.getchildren()
        empty_children = all(map(self.is_element_empty, children))
        text = el.text and el.text.strip(u'  \t\r\n\v\f\u00a0')
        return not text and empty_children

    def extra_clean(self, doc):
        for el in doc.xpath('//*[@href]'):
            href = el.attrib['href']
            if href and not href[0].isalpha():
                el.drop_tag()
                continue
            scheme, netloc, path, query, fragment = urlsplit(href)
            if scheme and scheme not in self.allowed_protocols:
                el.drop_tag()

        for attr in self.attr_val_is_uri:
            if attr == 'href':
                continue
            for el in doc.xpath('//*[@'+attr+']'):
                scheme, netloc, path, query, fragment = urlsplit(el.attrib[attr])
                scheme_fail = scheme and scheme not in self.allowed_protocols
                netloc_fail = not self.allow_external_src and netloc
                if scheme_fail or netloc_fail:
                    if attr == 'src':
                        el.drop_tag()
                    else:
                        el.attrib.pop(attr)

        if self.a_without_href:
            for link in doc.xpath('//a[not(@href)]'):
                link.drop_tag()

        if self.allow_classes is not None:
            for el in doc.xpath('//*[@class]'):
                classes = filter(None, el.attrib['class'].split())
                if el.tag in self.allow_classes:
                    allowed = self.allow_classes[el.tag]
                    condition = allowed if callable(allowed) else \
                            (lambda cls: cls in allowed)
                    classes = filter(condition, classes)
                else:
                    classes = []

                if classes:
                    el.attrib['class'] = ' '.join(classes)
                else:
                    el.attrib.pop('class')


        for callback in self.dom_callbacks:
            callback(doc)

        if self.wrap_inline_tags is not False and self.tags_to_wrap:
            self.clean_top(doc)

        for tag in self.drop_empty_tags:
            for el in doc.xpath('//'+tag):
                if not el.attrib and self.is_element_empty(el):
                    el.drop_tree()


def sanitize(value, **kwargs):
    doc = html.fragment_fromstring(value, create_parent=True)
    Cleaner(**kwargs)(doc)
    clean = html.tostring(doc, encoding='utf-8').decode('utf-8')
    return clean.split('>', 1)[1].rsplit('<', 1)[0]
