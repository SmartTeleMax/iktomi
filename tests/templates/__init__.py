import os
import unittest
from iktomi import web
from iktomi.templates import Template, TemplateError, BoundTemplate
from iktomi.templates.jinja2 import TemplateEngine


# class for mocking any objects with any properties
class MockClass(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TemplateTest(unittest.TestCase):

    def setUp(self):
        templates_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                                     'iktomi', 'templates', 'jinja2', 'templates')
        self.engine = TemplateEngine(templates_dir)
        self.template = Template(templates_dir, engines={'html':self.engine})

    def test_render_textarea(self):
        widget = MockClass(id=101,
                           classname="big",
                           input_name="big_input")
        rendered = self.template.render('widgets/textarea',
                                        widget=widget,
                                        readonly=True,
                                        value="Sample text")
        self.assertIn('<textarea', rendered)
        self.assertIn('id="101"', rendered)
        self.assertIn('class="big"', rendered)
        self.assertIn('name="big_input"', rendered)
        self.assertIn('readonly="readonly"', rendered)
        self.assertIn('>Sample text<', rendered)

    def test_resolve(self):
        filename, engine = self.template.resolve('widgets/textarea')
        self.assertEqual(filename, 'widgets/textarea.html')
        self.assertEqual(engine, self.engine)
        with self.assertRaises(TemplateError):
            self.template.resolve('nonexsistent/path')


class BoundTemplateTest(unittest.TestCase):

    def setUp(self):
        class TestingBoundTemplate(BoundTemplate):
            def get_template_vars(self):
                return {'readonly':True}

        templates_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                                     'iktomi', 'templates', 'jinja2', 'templates')
        self.engine = TemplateEngine(templates_dir)
        template = Template(templates_dir, engines={'html':self.engine})

        env = web.AppEnvironment.create()
        self.bound = TestingBoundTemplate(env, template)

    def test_engines(self):
        self.assertEqual(self.bound.engines.keys(), ['html'])
        self.assertEqual(self.bound.engines.values(), [self.engine])

    def test_vars(self):
        self.assertEqual(self.bound._vars(None), {'readonly':True})
        self.assertEqual(self.bound._vars({}), {'readonly':True})
        self.assertEqual(self.bound._vars({'foo':'bar'}),
                         {'readonly':True, 'foo':'bar'})
        env = web.AppEnvironment.create(foo='bar')
        self.assertEqual(self.bound._vars(env),
                         {'readonly':True, 'foo':'bar', 'request':None, 'root':None})

    def test_render(self):
        widget = MockClass(id=111,
                           classname="big",)
        rendered = self.bound.render('widgets/textarea',
                                        widget=widget,
                                        value="Sample text")
        self.assertIn('<textarea', rendered)
        self.assertIn('id="111"', rendered)
        self.assertIn('class="big"', rendered)
        self.assertIn('readonly="readonly"', rendered)
        self.assertIn('>Sample text<', rendered)

    def test_render_to_response(self):
        widget = MockClass(id=111,
                           classname="big",)
        response = self.bound.render_to_response('widgets/textarea',
                                                 {'widget':widget,
                                                  'value':"Sample text"})
        self.assertIn('text/html', response.headers['Content-Type'])

        rendered = response.body
        self.assertIn('<textarea', rendered)
        self.assertIn('id="111"', rendered)
        self.assertIn('class="big"', rendered)
        self.assertIn('readonly="readonly"', rendered)
        self.assertIn('>Sample text<', rendered)
