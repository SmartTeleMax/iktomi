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


class TestTinyMCE(TestFormClass):
    
    def test_init(self):
        # XXX test is not complete
        kwargs = dict(template='textinput',
                      classname='textinput',
                      plugins=['safari'],
                      buttons = (('bold', 'italic',), ('fullscreen', )),
                      browsers=('safari'),
                      cfg={'mode': 'exact'},
                      content_css='content_css', # ??
                      )
        
        widget = widgets.TinyMce(**kwargs)
        for key, value in kwargs.items():
            self.assertEqual(value, getattr(widget, key))

        widget = widget()
        for key, value in kwargs.items():
            self.assertEqual(value, getattr(widget, key))

    def test_init_add(self):
        # XXX test is not complete
        kwargs = dict(plugins=['safari'],
                      buttons=(('bold', 'italic',), ('fullscreen', )),
                      add_plugins=["textedit"],
                      add_buttons={0: ["underline"], 1: ['undo']},
                      drop_buttons=["bold"],
                      )
        
        result_kw = dict(plugins=('safari', "textedit"),
                         buttons=(('italic', 'underline'),
                                    ('fullscreen', 'undo')),
                        )
        
        widget = widgets.TinyMce(**kwargs)
        for key, value in result_kw.items():
            self.assertEqual(value, getattr(widget, key))

    def test_init_default(self):
        widget = widgets.TinyMce()
        for nm in 'buttons', 'plugins', 'browsers', 'cfg', 'content_css':
            self.assertEqual(getattr(widget, nm),
                             getattr(widgets.TinyMce, nm))
            assert nm in widget._init_kwargs
                 
if __name__ == '__main__':
    unittest.main()
