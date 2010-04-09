# -*- coding: utf-8 -*-

from ..utils import cached_property


class FormMedia(object):
    '''
    Instance encapsulating media items assigned to instances of
    :class:`Form <insanities.forms.form.Form>`,
    :class:`Field <insanities.forms.fields.Field>` and
    :class:`Widget <insanities.forms.widgets.Widget>`
    '''

    def __init__(self, items=[], env=None):
        self.env = env
        if isinstance(items, FormMedia):
            self._media = items._media
        else:
            self._media = []
        map(self._append, items)

    def _append(self, item):
        if item not in self._media:
            self._media.append(item(holder=self))

    def __iadd__(self, other):
        if isinstance(other, FormMedia):
            map(self._append, other._media)
        else:
            map(self._append, other)
        return self

    def __add__(self, other):
        media = FormMedia(self)
        media += other
        return media

    def __radd__(self, other):
        media = FormMedia(other)
        media += self
        return media

    def __iter__(self):
        return iter(self._media)

    @cached_property
    def macros(self):
        # XXX specific interface for jinja2?
        tmpl = self.env.get_template('forms/media')
        return tmpl.make_module(vars=self.env.locals)


class FormMediaAtom(object):
    '''
    Media item representing JS, CSS or some other media stuff linked to
    :class:`Form <insanities.forms.form.Form>` or it's parts.
    '''

    macro = None # Must be overwritten

    def __init__(self, data, holder=None):
        self.data = data
        self.holder = holder

    def __call__(self, holder):
        return type(self)(self.data, holder=holder)

    def __eq__(self, other):
        return type(self)==type(other) and self.data==other.data

    def __iter__(self):
        yield self

    def __add__(self, other):
        media = FormMedia(self)
        media += other
        return media

    def render(self):
        '''Renders media item to HTML'''
        return getattr(self.holder.macros, self.macro)(data=self.data)


class FormCSSRef(FormMediaAtom):

    macro = 'css_ref'


class FormCSSInline(FormMediaAtom):

    macro = 'css_inline'


class FormJSRef(FormMediaAtom):

    macro = 'js_ref'


class FormJSInline(FormMediaAtom):

    macro = 'js_inline'
