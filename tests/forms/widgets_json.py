# -*- coding: utf-8 -*-
import unittest
from os import path
from webob.multidict import MultiDict
from iktomi.utils.storage import VersionedStorage
from iktomi.templates import Template, BoundTemplate
from iktomi.templates import jinja2 as jnj
from iktomi.templates.jinja2 import TemplateEngine
import jinja2

from iktomi.forms import convs, media, perms, widgets_json as widgets
from iktomi.forms.form_json import Form, Field, FieldList, FieldSet, FieldBlock


class TestFormClass(unittest.TestCase):

    @property
    def env(self):
        # XXX: template is useless
        DIR = jnj.__file__
        DIR = path.dirname(path.abspath(DIR))
        TEMPLATES = [path.join(DIR, 'templates')]

        jinja_loader = TemplateEngine(TEMPLATES)
        template_loader = Template(engines={'html': jinja_loader},
                                            *TEMPLATES)
        env = VersionedStorage()
        env.template = BoundTemplate(env, template_loader)
        return env


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
    widget_name = 'TextInput'
    classname = 'textinput'

    def test_render(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget(classname="cls"))
            ]

        form = F(self.env)

        form.accept({'name': '<p>Paragraph</p>'})

        render = form.get_field('name').widget.render()
        self.assertEqual(render, {'widget': self.widget_name,
                                  'multiple': False,
                                  'hint': u'',
                                  'renders_hint': False,
                                  'required': False,
                                  'render_type': 'default',
                                  'label': u'',
                                  'classname': 'cls',
                                  'key':'name',
                                  'readonly':False,
                                  'safe_hint': False,
                                  'safe_label': False})

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
        form.accept({'name': '<p>Paragraph</p>'})
        render = form.get_field('name').widget.render()
        self.assertEqual(render, {'widget': self.widget_name,
                                  'multiple': False,
                                  'hint': u'',
                                  'renders_hint': False,
                                  'required': False,
                                  'render_type': 'default',
                                  'label': u'',
                                  'classname': self.classname,
                                  'key':'name',
                                  'readonly':True,
                                  'safe_hint': False,
                                  'safe_label': False})


class TestTextarea(TestTextInput):

    widget = widgets.Textarea
    widget_name = 'Textarea'
    classname = ''

    def test_render(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget())
            ]

        form = F(self.env)

        form.accept({'name': '</textarea>'})
        render = form.get_field('name').widget.render()
        self.assertEqual(render, {'widget': 'Textarea',
                                  'multiple': False,
                                  'hint': u'',
                                  'renders_hint': False,
                                  'required': False,
                                  'render_type': 'default',
                                  'label': u'',
                                  'classname': self.classname,
                                  'key':'name',
                                  'readonly':False,
                                  'safe_hint': False,
                                  'safe_label': False})


class TestPasswordInput(TestTextInput):

    widget=widgets.PasswordInput
    widget_name = 'PasswordInput'
    classname='textinput'


class TestHiddenInput(TestFormClass):

    widget = widgets.HiddenInput
    widget_name = 'HiddenInput'

    def test_render(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget())
            ]

        form = F(self.env)

        form.accept({'name': 'hidden value'})
        render = form.get_field('name').widget.render()
        self.assertEqual(render, {'widget': 'HiddenInput',
                                  'multiple': False,
                                  'hint': u'',
                                  'renders_hint': False,
                                  'required': False,
                                  'render_type': 'hidden',
                                  'label': u'',
                                  'classname': '',
                                  'key':'name',
                                  'readonly':False,
                                  'safe_hint': False,
                                  'safe_label': False})


class TestCheckBox(TestFormClass):

    widget = widgets.CheckBox

    def test_render(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Bool(),
                      widget=self.widget())
            ]

        form = F(self.env)
        form.accept({'name': ''})
        render = form.get_field('name').widget.render()
        self.assertFalse(render['checked'])

        form.accept({'name': 'checked'})
        render = form.get_field('name').widget.render()
        self.assertTrue(render['checked'])


class TestSelect(TestFormClass):

    choices = [
        ('1', 'first'),
        ('2', 'second'),
    ]
    widget = widgets.Select

    def test_render_not_required(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.EnumChoice(choices=self.choices,
                                            required=False),
                      widget=self.widget())
            ]

        form = F(self.env)

        form.accept({'name': '1'})
        render = form.get_field('name').widget.render()
        self.assertEqual(render['null_label'], '--------')
        options = render['options']
        self.assertEqual(options, [{'value':'1', 'title': 'first'},
                                   {'value':'2', 'title': 'second'}])
        self.assertFalse(render['required'])

    def test_render_required(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.EnumChoice(choices=self.choices,
                                            required=True),
                      widget=self.widget())
            ]

        form = F(self.env)

        form.accept({'name': '1'})
        render = form.get_field('name').widget.render()
        self.assertEqual(render['null_label'], '--------')
        options = render['options']
        self.assertEqual(options, [{'value':'1', 'title': 'first'},
                                   {'value':'2', 'title': 'second'}])
        self.assertTrue(render['required'])

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
        render = form.get_field('name').widget.render()
        self.assertTrue(render['multiple'])


class TestCheckBoxSelect(TestSelect):

    widget = widgets.CheckBoxSelect


class TestCharDisplay(TestFormClass):

    widget = widgets.CharDisplay

    def test_render(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget())
            ]

        form = F(self.env)
        render = form.get_field('name').widget.render()
        self.assertEqual(render['value'], None)
        self.assertEqual(render['should_escape'], True)

        form.accept({'name':'one two three'})
        render = form.get_field('name').widget.render()
        self.assertEqual(render['value'], 'one two three')
        self.assertEqual(render['should_escape'], True)

    def test_transform(self):
        class F(Form):
            fields = [
                Field('name',
                      conv=convs.Char(),
                      widget=self.widget(getter=lambda x: x.replace('two', 'four')))
            ]

        form = F(self.env)
        self.assertRaises(AttributeError, form.get_field('name').widget.render)

        form.accept({'name':'one two three'})
        render = form.get_field('name').widget.render()
        self.assertEqual(render['value'], 'one four three')
        self.assertEqual(render['should_escape'], True)


class TestFieldList(TestFormClass):

    def test_render_simple(self):
        class F(Form):
            fields = [
                FieldList('list',
                          field=Field('name',
                                      conv=convs.Char(),
                                      widget=widgets.TextInput))
            ]

        form = F(self.env)
        render = form.get_field('list').widget.render()
        self.assertEqual(render['subwidget'], {
            'widget': 'TextInput',
            'multiple': False,
            'hint': u'',
            'renders_hint': False,
            'required': False,
            'render_type': 'default',
            'label': u'',
            'classname': 'textinput',
            'key':'name',
            'readonly':False,
            'safe_hint': False,
            'safe_label': False})


    def test_render_fieldlist_of_fieldsets(self):
        class F(Form):
            fields = [
                FieldList('list',
                          field=FieldSet(None, fields=[
                              Field('name',
                                      conv=convs.Char(),
                                      widget=widgets.TextInput)]))
            ]

        form = F(self.env)
        render = form.get_field('list').widget.render()
        self.assertEqual(render['subwidget']['widget'], 'FieldSetWidget')
        fieldset = render['subwidget']
        self.assertEqual(fieldset['widgets'], [{
            'widget': 'TextInput',
            'multiple': False,
            'hint': u'',
            'renders_hint': False,
            'required': False,
            'render_type': 'default',
            'label': u'',
            'classname': 'textinput',
            'key':'name',
            'readonly':False,
            'safe_hint': False,
            'safe_label': False
        }])


class TestFieldSetWidget(TestFormClass):

    def test_render(self):
        class F(Form):
            fields = [
               FieldSet('login', fields=[
                            Field('name',
                                  conv=convs.Char(),
                                  widget=widgets.TextInput),
                            Field('password',
                                  conv=convs.Char(),
                                  widget=widgets.PasswordInput)
               ])
            ]

        form = F(self.env)
        render = form.get_field('login').widget.render()
        self.assertEqual(render['widget'], 'FieldSetWidget')
        self.assertEqual(render['widgets'][0]['widget'], 'TextInput')
        self.assertEqual(render['widgets'][0]['key'], 'name')

        self.assertEqual(render['widgets'][1]['widget'], 'PasswordInput')
        self.assertEqual(render['widgets'][1]['key'], 'password')


class TestFieldBlockWidget(TestFormClass):

    def test_render(self):
        class F(Form):
            fields = [
               FieldBlock(None, fields=[
                            Field('name',
                                  conv=convs.Char(),
                                  widget=widgets.TextInput),
                            Field('password',
                                  conv=convs.Char(),
                                  widget=widgets.PasswordInput)
               ])
            ]

        form = F(self.env)
        render = form.fields[0].widget.render()
        self.assertEqual(render['widget'], 'FieldBlockWidget')
        self.assertEqual(render['render_type'], 'full-width')
        self.assertEqual(render['widgets'][0]['widget'], 'TextInput')
        self.assertEqual(render['widgets'][0]['key'], 'name')

        self.assertEqual(render['widgets'][1]['widget'], 'PasswordInput')
        self.assertEqual(render['widgets'][1]['key'], 'password')


class TestFileInput(TestTextInput):

    widget=widgets.FileInput
    widget_name = 'FileInput'
    classname=''
