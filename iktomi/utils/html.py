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

    wrap_inline_tags = False
    # Tags to wrap in paragraphs on top 
    wrap_in_p = ['b', 'big', 'i', 'small', 'tt',
                 'abbr', 'acronym', 'cite', 'code',
                 'dfn', 'em', 'kbd', 'strong', 'samp',
                 'var', 'a', 'bdo', 'br', 'map', 'object',
                 'q', 'span', 'sub', 'sup']

    def __call__(self, doc):
        clean.Cleaner.__call__(self, doc)
        if hasattr(doc, 'getroot'):
            # ElementTree instance, instead of an element
            doc = doc.getroot()
        self.extra_clean(doc)

    def clean_top(self, doc):
        par = None
        first_par = False
        # create paragraph if there text in the beginning of top
        if (doc.text or "").strip():
            par = html.Element('p')
            doc.insert(0, par)
            par.text = doc.text
            doc.text = None
            # remember if first paragraph created from text
            first_par = True

        for child in doc.getchildren():
            i = doc.index(child)

            if child.tag == 'br' and 'br' in self.wrap_in_p:
                if (child.tail or "").strip():
                    par = html.Element('p')
                    doc.insert(i, par)
                    par.text = child.tail
                doc.remove(child)
                continue

            if child.tag not in self.wrap_in_p and \
                    (child.tail or "").strip():
                par = html.Element('p')
                par.text = child.tail
                child.tail = None
                doc.insert(i+1, par)
                continue

            if child.tag in self.wrap_in_p:
                if par is None:
                    par = html.Element('p')
                    doc.insert(i, par)
                par.append(child)
            else:
                if first_par and i == 0:
                    continue
                par = None

    def extra_clean(self, doc):
        for el in doc.xpath('//*[@href]'):
            scheme, netloc, path, query, fragment = urlsplit(el.attrib['href'])
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

        for tag in self.drop_empty_tags:
            for el in doc.xpath('//'+tag+'[not(./*)]'):
                has_text = el.text and el.text.strip(u'  \t\r\n\v\f\u00a0')
                if not el.attrib and not has_text:
                    el.drop_tag()

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

        if self.wrap_inline_tags and self.wrap_in_p:
            self.clean_top(doc)


def sanitize(value, **kwargs):
    doc = html.fragment_fromstring(value, create_parent=True)
    Cleaner(**kwargs)(doc)
    clean = html.tostring(doc, encoding='utf-8').decode('utf-8')
    return clean.split('>', 1)[1].rsplit('<', 1)[0]
