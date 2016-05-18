# -*- coding: utf-8 -*-
import six
import unittest
from os import path
from webob.multidict import MultiDict
from iktomi.utils.storage import VersionedStorage
from iktomi.templates import Template, BoundTemplate
from iktomi.templates import jinja2 as jnj
from iktomi.templates.jinja2 import TemplateEngine
import jinja2
from lxml import html

from iktomi.forms import fields, convs, widgets, perms, \
                         Form, Field, FieldList, FieldSet


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
        #print value
        return html.fragment_fromstring(value, create_parent=True)


class TestWidget(TestFormClass):

    def test_init(self):
        kwargs = dict(template='textinput', classname='textinput')

        widget = widgets.Widget(**kwargs)
        for key, value in kwargs.items():
            self.assertEqual(value, getattr(widget, key))

        widget = widget()
        for key, value in kwargs.items():
            self.assertEqual(value, getattr(widget, key))

    def test_obsolete(self):
        with self.assertRaises(TypeError) as exc:
            widgets.Widget(template='checkbox', multiple=True)
        exc = exc.exception
        self.assertIn('Obsolete parameters are used', str(exc))
        self.assertIn('multiple', str(exc))


class TestTextInput(TestFormClass):

    widget = widgets.TextInput
    tag = 'input'

    def get_value(self, html):
        return html.xpath('.//'+self.tag+'/@value')[0]

    def test_render(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget(classname="cls")),
                Field('unreadable',
                      permissions="w",
                      conv=convs.Char(),
                      widget=self.widget(classname="cls"))
            ]

        form = F(self.env)

        form.raw_data = MultiDict({'name': '<p>Paragraph</p>'})
        render = form.get_field('name').widget.render()
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, '<p>Paragraph</p>')
        self.assertEqual(html.xpath('.//'+self.tag+'/@readonly'), [])
        self.assertEqual(html.xpath('.//'+self.tag+'/@class'), ['cls'])
        render = form.get_field('unreadable').widget.render()
        self.assertEqual(render, '')

    def test_escape(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget())
            ]

        form = F(self.env)

        form.raw_data = MultiDict({'name': jinja2.Markup('<p>Paragraph</p>')})
        render = form.get_field('name').widget.render()
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, '<p>Paragraph</p>')
        self.assert_('&lt;p&gt;Paragraph&lt;/p&gt;' in six.text_type(render), render)


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

        form.raw_data = MultiDict({'name': '<p>Paragraph</p>'})
        render = form.get_field('name').widget.render()
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, '<p>Paragraph</p>')
        self.assertEqual(html.xpath('.//'+self.tag+'/@readonly'), ['readonly'])


class TestTextarea(TestTextInput):

    widget = widgets.Textarea
    tag = 'textarea'

    def get_value(self, html):
        return ''.join(html.xpath('.//'+self.tag+'/text()'))

    def test_escape(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget())
            ]

        form = F(self.env)

        form.raw_data = MultiDict({'name': jinja2.Markup('</textarea>')})
        render = form.get_field('name').widget.render()
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, '</textarea>')
        self.assert_('&lt;/textarea&gt;' in six.text_type(render), render)


class TestCheckBox(TestFormClass):

    widget = widgets.CheckBox
    tag = 'input'

    def get_value(self, html):
        return bool(html.xpath('.//'+self.tag+'/@checked'))

    def test_render(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Bool(),
                      widget=self.widget())
            ]

        form = F(self.env)
        form.raw_data = MultiDict({'name': ''})
        render = form.get_field('name').widget.render()
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, False)

        form.raw_data = MultiDict({'name': 'checked'})
        render = form.get_field('name').widget.render()
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, True)


class TestHiddenInput(TestFormClass):

    widget = widgets.HiddenInput
    tag = 'input'

    def get_value(self, html):
        return html.xpath('.//'+self.tag+'/@value')[0]

    def test_render(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget())
            ]

        form = F(self.env)

        form.raw_data = MultiDict({'name': 'hidden value'})
        render = form.get_field('name').widget.render()
        html = self.parse(render)
        value = self.get_value(html)
        self.assertEqual(value, 'hidden value')



class TestCharDisplay(TestFormClass):

    widget = widgets.CharDisplay
    tag = 'span'

    def get_value(self, html):
        return ''.join(html.xpath('.//'+self.tag+'/text()'))

    def test_render(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget())
            ]

        form = F(self.env)

        form.raw_data = MultiDict({'name': '<p>char display</p>'})
        render = form.get_field('name').widget.render()
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

        form.raw_data = MultiDict({'name': '<i>char display</i>'})
        render = form.get_field('name').widget.render()
        html = self.parse(render)
        value = ''.join(html.xpath('.//'+self.tag+'/i/text()'))
        self.assertEqual(value, 'char display')

    def test_transform(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget(getter=lambda x: x.replace('value', 'display')))
            ]

        form = F(self.env)

        form.raw_data = MultiDict({'name': 'char value'})
        render = form.get_field('name').widget.render()
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
        return [(x.attrib['value'],
                 x.text,
                 'selected' in x.attrib)
                 for x in html.xpath('.//option')]

    def check_multiple(self, html):
        self.assertEqual(html.xpath('.//select/@multiple'),
                         ['multiple'])

    def check_not_multiple(self, html):
        self.assertEqual(html.xpath('.//select/@multiple'),
                         [])

    def test_render_not_required(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.EnumChoice(choices=self.choices,
                                            required=False),
                      widget=self.widget())
            ]

        form = F(self.env)

        form.raw_data = MultiDict({'name': '1'})
        render = form.get_field('name').widget.render()
        html = self.parse(render)
        self.check_not_multiple(html)
        options = self.get_options(html)
        self.assertEqual(options, [('', self.widget.null_label, False),
                                   ('1', 'first', True),
                                   ('2', 'second', False)])

        form.raw_data = MultiDict({'name': ''})
        render = form.get_field('name').widget.render()
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

        form.raw_data = MultiDict({'name': '1'})
        render = form.get_field('name').widget.render()
        html = self.parse(render)
        self.check_not_multiple(html)
        options = self.get_options(html)
        self.assertEqual(options, [('1', 'first', True),
                                   ('2', 'second', False)])

        form.raw_data = MultiDict({'name': ''})
        render = form.get_field('name').widget.render()
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

        form.raw_data = MultiDict([('name', '1'), ('name', '2')])
        render = form.get_field('name').widget.render()
        html = self.parse(render)
        self.check_multiple(html)
        options = self.get_options(html)
        self.assertEqual(options, [('1', 'first', True),
                                   ('2', 'second', True)])

        form.raw_data = MultiDict()
        render = form.get_field('name').widget.render()
        html = self.parse(render)
        options = self.get_options(html)
        self.assertEqual(options, [('1', 'first', False),
                                   ('2', 'second', False)])

    def test_render_enum_boolean(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.EnumChoice(conv=convs.Bool(),
                                            required=True,
                                            choices=[(False, u'no'),
                                                     (True, u'yes')]),
                      initial=False,
                      widget=self.widget())
            ]

        form = F(self.env)
        render = form.get_field('name').widget.render()
        html = self.parse(render)
        options = self.get_options(html)
        self.assertEqual(options, [('', 'no', True),
                                   ('checked', 'yes', False)])


class TestCheckBoxSelect(TestSelect):

    widget = widgets.CheckBoxSelect

    def get_options(self, html):
        return [(x.attrib['value'],
                 x.getparent().xpath('./label/text()')[0],
                 'checked' in x.attrib)
                for x in html.xpath('.//input')]

    def check_multiple(self, html):
        self.assertEqual(html.xpath('.//input/@type')[0],
                         'checkbox')

    def check_not_multiple(self, html):
        self.assertEqual(html.xpath('.//input/@type')[0],
                         'radio')

class TestFieldList(TestFormClass):

    def test_render(self):
        class F(Form):
            fields = [
                FieldList('list',
                          field=FieldSet(None, fields=[
                              Field('name',
                                     conv=convs.Char(),
                                     widget=widgets.TextInput)]))
            ]

        form = F(self.env)
        form.accept(MultiDict((('list-indices','1'),
                               ('list-indices', '2'),
                               ('list.1.name', 'First' ),
                               ('list.2.name', 'Second' )))
                    )

        render = form.get_field('list').widget.render()
        self.assertIn('<table class="fieldlist" id="list">', render)
        self.assertIn('<input', render)
        self.assertIn('value="1"', render)
        self.assertIn('value="2"', render)
        self.assertIn('First', render)
        self.assertIn('Second', render)

        template = form.get_field('list').widget.render_template_field()
        self.assertIn('id="list.%list-index%.name"', template)
        self.assertNotIn('First', template)
        self.assertNotIn('Second', template)
