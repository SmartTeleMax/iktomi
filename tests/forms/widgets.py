# -*- coding: utf-8 -*-
import unittest
from copy import copy

from insanities.forms import fields, convs, form, widgets, media, perms


class TestFormClass(unittest.TestCase):
    def setUp(self):
        pass
    
    @property
    def env(self):
        from os import path
        import jinja2
        from insanities.ext import jinja2 as jnj

        DIR = jnj.__file__
        DIR = path.dirname(path.abspath(DIR))
        TEMPLATES = [path.join(DIR, 'templates')]
        
        
        template_loader = jinja2.Environment(
                            loader=jinja2.FileSystemLoader(TEMPLATES))
        return jnj.FormEnvironment(template_loader)


class TestWidget(TestFormClass):

    def test_init(self):
        kwargs = dict(template='textinput', classname='textinput')

        widget = widgets.Widget(**kwargs)
        for key, value in kwargs.items():
            self.assertEqual(value, getattr(widget, key))

        widget = widget()
        for key, value in kwargs.items():
            self.assertEqual(value, getattr(widget, key))


if __name__ == '__main__':
    unittest.main()
