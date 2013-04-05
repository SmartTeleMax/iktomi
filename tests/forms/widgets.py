# -*- coding: utf-8 -*-
import unittest
from os import path
from html5lib import HTMLParser, treebuilders
from iktomi.utils.storage import VersionedStorage
from iktomi.templates import Template, BoundTemplate
from iktomi.templates import jinja2 as jnj
from iktomi.templates.jinja2 import TemplateEngine
import jinja2
import xpath

from iktomi.forms import fields, convs, widgets, media, perms, \
                         Form, Field


class TestFormClass(unittest.TestCase):
    def setUp(self):
        pass
    
    @property
    def env(self):
        DIR = jnj.__file__
        DIR = path.dirname(path.abspath(DIR))
        TEMPLATES = [path.join(DIR, 'templates')]

        jinja_loader = TemplateEngine(TEMPLATES)
        template_loader = Template(engines={'html': jinja_loader},
                                            *TEMPLATES)
        env = VersionedStorage()
        env.template = BoundTemplate(env, template_loader)
        return env

    def parse(self, value):
        print value
        p = HTMLParser(tree=treebuilders.getTreeBuilder("dom"))
        return p.parseFragment(value)


class TestWidget(TestFormClass):

    def test_init(self):
        kwargs = dict(template='textinput', classname='textinput')

        widget = widgets.Widget(**kwargs)
        for key, value in kwargs.items():
            self.assertEqual(value, getattr(widget, key))

        widget = widget()
        for key, value in kwargs.items():
            self.assertEqual(value, getattr(widget, key))


class TestTextInput(TestFormClass):

    widget = widgets.TextInput
    tag = 'input'

    def get_value(self, html):
        return xpath.findvalue('.//*:%s/@value'%self.tag, html)

    def test_render(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget(classname="cls"))
            ]

        form = F(self.env)

        render = form.get_field('name').widget.render('<p>Paragraph</p>')
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, '<p>Paragraph</p>')
        self.assertEqual(xpath.findvalue('.//*:%s/@readonly'%self.tag, html), None)
        self.assertEqual(xpath.findvalue('.//*:%s/@class'%self.tag, html), 'cls')

    def test_escape(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget())
            ]

        form = F(self.env)

        render = form.get_field('name').widget.render(jinja2.Markup('<p>Paragraph</p>'))
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, '<p>Paragraph</p>')
        self.assert_('&lt;p&gt;Paragraph&lt;/p&gt;' in unicode(render), render)


    def test_render_readonly(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget(),
                      permissions="r",
                      )
            ]

        form = F(self.env)

        render = form.get_field('name').widget.render('<p>Paragraph</p>')
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, '<p>Paragraph</p>')
        self.assertEqual(xpath.findvalue('.//*:%s/@readonly'% self.tag, html), 'readonly')


class TestTextarea(TestTextInput):

    widget = widgets.Textarea
    tag = 'textarea'

    def get_value(self, html):
        return ''.join(xpath.findvalues('.//*:%s/text()'%self.tag, html))

    def test_escape(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget())
            ]

        form = F(self.env)

        render = form.get_field('name').widget.render(jinja2.Markup('</textarea>'))
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, '</textarea>')
        self.assert_('&lt;/textarea&gt;' in unicode(render), render)


class TestCheckBox(TestFormClass):

    widget = widgets.CheckBox
    tag = 'input'

    def get_value(self, html):
        return xpath.findvalue('.//*:%s/@checked'%self.tag, html)

    def test_render(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Bool(),
                      widget=self.widget())
            ]

        form = F(self.env)

        render = form.get_field('name').widget.render('')
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, None)

        render = form.get_field('name').widget.render('checked')
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, 'checked')


class TestHiddenInput(TestFormClass):

    widget = widgets.HiddenInput
    tag = 'input'

    def get_value(self, html):
        return xpath.findvalue('.//*:%s/@value'%self.tag, html)

    def test_render(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget())
            ]

        form = F(self.env)

        render = form.get_field('name').widget.render('hidden value')
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, 'hidden value')



class TestCharDisplay(TestFormClass):

    widget = widgets.CharDisplay
    tag = 'span'

    def get_value(self, html):
        return ''.join(xpath.findvalues('.//*:%s/text()'%self.tag, html))

    def test_render(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget())
            ]

        form = F(self.env)

        render = form.get_field('name').widget.render('<p>char display</p>')
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, '<p>char display</p>')

    def test_not_escape(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget(escape=False))
            ]

        form = F(self.env)

        render = form.get_field('name').widget.render('<i>char display</i>')
        html = self.parse(render)
        value = ''.join(xpath.findvalues('.//*:%s/*:i/text()'%self.tag, html))
        self.assertEqual(value, 'char display')

    def test_transform(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget(getter=lambda x: x.replace('value', 'display')))
            ]

        form = F(self.env)

        render = form.get_field('name').widget.render('char value')
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, 'char display')


class TestSelect(TestFormClass):

    choices = [
        ('1', 'first'),
        ('2', 'second'),
    ]
    widget = widgets.Select

    def get_options(self, html):
        return [(x.getAttribute('value'),
                 x.childNodes[0].data,
                 x.hasAttribute('selected'))
                 for x in xpath.find('.//*:option', html)]

    def check_multiple(self, html):
        self.assertEqual(xpath.findvalue('.//*:select/@multiple', html),
                         'multiple')

    def check_not_multiple(self, html):
        self.assertEqual(xpath.findvalue('.//*:select/@multiple', html),
                         None)

    def test_render_not_required(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.EnumChoice(choices=self.choices,
                                            required=False),
                      widget=self.widget())
            ]

        form = F(self.env)

        render = form.get_field('name').widget.render('1')
        html = self.parse(render)
        self.check_not_multiple(html)
        options = self.get_options(html)
        self.assertEqual(options, [('', self.widget.null_label, False),
                                   ('1', 'first', True),
                                   ('2', 'second', False)])

        render = form.get_field('name').widget.render(None)
        html = self.parse(render)
        options = self.get_options(html)
        self.assertEqual(options, [('', self.widget.null_label, True),
                                   ('1', 'first', False),
                                   ('2', 'second', False)])

    def test_render_required(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.EnumChoice(choices=self.choices,
                                            required=True),
                      widget=self.widget())
            ]

        form = F(self.env)

        render = form.get_field('name').widget.render('1')
        html = self.parse(render)
        self.check_not_multiple(html)
        options = self.get_options(html)
        self.assertEqual(options, [('1', 'first', True),
                                   ('2', 'second', False)])

        render = form.get_field('name').widget.render(None)
        html = self.parse(render)
        options = self.get_options(html)
        self.assertEqual(options, [('', self.widget.null_label, True),
                                   ('1', 'first', False),
                                   ('2', 'second', False)])

    def test_render_multiple(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.ListOf(
                          convs.EnumChoice(choices=self.choices,
                                           required=True)),
                      widget=self.widget())
            ]

        form = F(self.env)

        render = form.get_field('name').widget.render(['1', '2'])
        html = self.parse(render)
        self.check_multiple(html)
        options = self.get_options(html)
        self.assertEqual(options, [('1', 'first', True),
                                   ('2', 'second', True)])

        render = form.get_field('name').widget.render([])
        html = self.parse(render)
        options = self.get_options(html)
        self.assertEqual(options, [('1', 'first', False),
                                   ('2', 'second', False)])


class TestCheckBoxSelect(TestSelect):

    widget = widgets.CheckBoxSelect

    def get_options(self, html):
        return [(x.getAttribute('value'),
                 xpath.findvalue('./*:label/text()', x.parentNode),
                 x.hasAttribute('checked'))
                for x in xpath.find('.//*:input', html)]

    def check_multiple(self, html):
        self.assertEqual(xpath.findvalue('.//*:input/@type', html),
                         'checkbox')

    def check_not_multiple(self, html):
        self.assertEqual(xpath.findvalue('.//*:input/@type', html),
                         'radio')


if __name__ == '__main__':
    unittest.main()
