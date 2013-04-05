# -*- coding: utf-8 -*-
import unittest
from os import path
from html5lib import HTMLParser, treebuilders
from iktomi.utils.storage import VersionedStorage
from iktomi.templates import Template, BoundTemplate
from iktomi.templates import jinja2 as jnj
from iktomi.templates.jinja2 import TemplateEngine
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

class TestSelect(TestFormClass):

    choices = [
        ('1', 'first'),
        ('2', 'second'),
    ]

    def get_options(self, html):
        return [(x.getAttribute('value'),
                 x.childNodes[0].data,
                 x.hasAttribute('selected'))
                 for x in xpath.find('.//*:option', html)]

    def test_render_not_required(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.EnumChoice(choices=self.choices,
                                            required=False),
                      widget=widgets.Select())
            ]

        form = F(self.env)

        render = form.get_field('name').widget.render('1')
        html = self.parse(render)
        options = self.get_options(html)
        self.assertEqual(options, [('', widgets.Select.null_label, False),
                                   ('1', 'first', True),
                                   ('2', 'second', False)])

        render = form.get_field('name').widget.render(None)
        html = self.parse(render)
        options = self.get_options(html)
        self.assertEqual(options, [('', widgets.Select.null_label, True),
                                   ('1', 'first', False),
                                   ('2', 'second', False)])

    def test_render_required(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.EnumChoice(choices=self.choices,
                                            required=True),
                      widget=widgets.Select())
            ]

        form = F(self.env)

        render = form.get_field('name').widget.render('1')
        html = self.parse(render)
        options = self.get_options(html)
        self.assertEqual(options, [('1', 'first', True),
                                   ('2', 'second', False)])

        render = form.get_field('name').widget.render(None)
        html = self.parse(render)
        options = self.get_options(html)
        self.assertEqual(options, [('', widgets.Select.null_label, True),
                                   ('1', 'first', False),
                                   ('2', 'second', False)])

    def test_render_multiple(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.ListOf(
                          convs.EnumChoice(choices=self.choices,
                                           required=True)),
                      widget=widgets.Select())
            ]

        form = F(self.env)

        render = form.get_field('name').widget.render(['1', '2'])
        html = self.parse(render)
        self.assertEqual(xpath.findvalue('.//*:select/@multiple', html),
                         'multiple')
        options = self.get_options(html)
        self.assertEqual(options, [('1', 'first', True),
                                   ('2', 'second', True)])

        render = form.get_field('name').widget.render([])
        html = self.parse(render)
        options = self.get_options(html)
        self.assertEqual(options, [('1', 'first', False),
                                   ('2', 'second', False)])




if __name__ == '__main__':
    unittest.main()
