# -*- coding: utf-8 -*-

import unittest

from web.app import AppEnvironment
from iktomi.forms import Form, Field, FieldSet
from iktomi.unstable.forms import convs
from iktomi.utils import cached_property

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, orm, create_engine
from iktomi.db.sqla.declarative import AutoTableNameMeta

Base = declarative_base(metaclass=AutoTableNameMeta)


class ChoiceObject(Base):

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    name = Column(String(200))

class SlugObject(Base):

    id = Column(String(10), primary_key=True)
    title = Column(String(200))


def init_conv(conv, name='name'):
    class F(Form):
        fields = [Field(name, conv)]
    env = AppEnvironment.create()
    return F(env).get_field(name).conv


class EmailConvTests(unittest.TestCase):

    def test_email(self):
        conv = init_conv(convs.Email)
        email = '-!#$%&\'*+/=?^_`{}.a0@example.com'
        value = conv.accept(email)
        self.assertEqual(value, email)

    def test_strip(self):
        conv = init_conv(convs.Email)
        # Vertical tab ('\v' or '\xob') is whitespace too, but it's not safe
        # for XML and HTML, so it's replaced.
        value = conv.accept(' \t\r\nname@example.com \t\r\n')
        self.assertEqual(value, u'name@example.com')

    def test_non_text(self):
        for c in u'\x00\x08\x0B\x0C\x0E\x0F\uD800\uDFFF':
            conv = init_conv(convs.Email)
            value = conv.accept(u'name@example.com'+c)
            self.assertEqual(value, None)
            self.assertEqual(conv.field.form.errors.keys(), [conv.field.name])

    def test_invalid(self):
        for email in ['name@com',
                      '@example.com',
                      'example.com',
                      'name@127.0.0.1',
                      'name@example.i',
                      'name@example.123',
                      '.name@example.com',
                      'name.@example.com',
                      'na..me@example.com']:
            conv = init_conv(convs.Email)
            value = conv.accept('name@com')
            self.assertEqual(value, None)
            self.assertEqual(conv.field.form.errors.keys(), [conv.field.name])


class M(object):

    a = b = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)



class ModelDictConvTests(unittest.TestCase):

    def _get_form(self, *a, **kw):
        class F(Form):
            fields = [
                FieldSet('fs',
                         conv=convs.ModelDictConv(*a, **kw),
                         fields=[Field('a'), Field('b')]),
            ]
        return F

    def _init_modeldict_conv(self, *a, **kw):
        kw.setdefault('model', M)
        F = self._get_form(*a, **kw)
        return F(self.env).get_field('fs').conv

    @cached_property
    def env(self):
        return AppEnvironment.create()

    def test_to_python(self):
        conv = self._init_modeldict_conv()
        obj = conv.to_python({'a': 1, 'b': '2', 'c': 3})
        self.assertEqual(obj.a, 1)
        self.assertEqual(obj.b, '2')
        self.assertFalse(hasattr(obj, 'c'))

    def test_to_python(self):
        conv = self._init_modeldict_conv()
        obj = conv.to_python({'a': 1, 'b': '2', 'c': 3})
        self.assertEqual(obj.a, 1)
        self.assertEqual(obj.b, '2')
        self.assertFalse(hasattr(obj, 'c'))

    def test_validation_error(self):
        def validate(field, value):
            raise convs.ValidationError('')
        conv = self._init_modeldict_conv(validate)
        obj = conv.accept({'a': 1, 'b': '2', 'c': 3})
        self.assertEqual(obj.__class__.__name__, 'M')
        self.assertEqual(obj.a, None)
        self.assertEqual(obj.b, None)
        self.assertFalse(hasattr(obj, 'c'))

    def test_from_python(self):
        conv = self._init_modeldict_conv()
        obj = conv.model(a=1, b='2', c=3)
        value = conv.from_python(obj)
        self.assertEqual(value, {'a': 1, 'b': '2'})

    def test_none_object(self):
        F = self._get_form(required=False, model=M)
        form = F(self.env, initial={'fs': None})

        self.assertEqual(dict(form.raw_data), {})


class ModelChoiceTests(unittest.TestCase):

    def setUp(self):
        engine = create_engine('sqlite://')
        Base.metadata.create_all(engine)
        Session = orm.sessionmaker()
        self.db = Session(bind=engine)
        self.env.db = self.db

        self.db.add_all([
            ChoiceObject(id=1, title="title1", name="name1"),
            ChoiceObject(id=2, title="title2", name="name2"),
            ChoiceObject(id=3, title="title3", name="name3"),
            SlugObject(title="title1", id="slug1"),
            SlugObject(title="title2", id="slug2"),
            SlugObject(title="title3", id="slug3"),
        ])
        self.db.commit()

    def _get_form(self, *a, **kw):
        conv = convs.ModelChoice(*a, **kw)
        if kw.pop('multiple', False):
            conv = convs.ListOf(conv)

        class F(Form):
            fields = [
                Field('obj',
                      conv=conv),
            ]
        return F

    def _init_modelchoice_conv(self, *a, **kw):
        kw.setdefault('model', ChoiceObject)
        F = self._get_form(*a, **kw)
        return F(self.env).get_field('obj').conv

    @cached_property
    def env(self):
        return AppEnvironment.create()

    def test_to_python(self):
        conv = self._init_modelchoice_conv(conv=convs.Int())

        self.assertEqual(conv.to_python('1').title, 'title1')
        self.assertEqual(conv.to_python('2').title, 'title2')
        self.assertEqual(conv.to_python(''), None)
        self.assertEqual(conv.to_python('-1'), None)
        self.assertEqual(conv.to_python('100'), None)
        self.assertEqual(conv.to_python('aaa'), None)


    def test_from_python(self):
        conv = self._init_modelchoice_conv(conv=convs.Int())

        obj = self.db.query(ChoiceObject).get(1)
        value = conv.from_python(obj)
        self.assertEqual(value, '1')

    def test_options(self):
        conv = self._init_modelchoice_conv(conv=convs.Int())

        self.assertEqual(list(conv.options()), [
            ('1', 'title1'),
            ('2', 'title2'),
            ('3', 'title3'),
        ])

    def test_title_field(self):
        conv = self._init_modelchoice_conv(conv=convs.Int(), title_field="name")

        self.assertEqual(list(conv.options()), [
            ('1', 'name1'),
            ('2', 'name2'),
            ('3', 'name3'),
        ])

    def test_condition_expr(self):
        conv = self._init_modelchoice_conv(conv=convs.Int(), condition=ChoiceObject.id>1)

        self.assertEqual(list(conv.options()), [
            ('2', 'title2'),
            ('3', 'title3'),
        ])

    def test_condition_dict(self):
        conv = self._init_modelchoice_conv(conv=convs.Int(), condition={'id': 2})

        self.assertEqual(list(conv.options()), [
            ('2', 'title2'),
        ])

    def test_slug(self):
        conv = self._init_modelchoice_conv(conv=convs.Char(), model=SlugObject)

        self.assertEqual(conv.to_python('slug1').title, 'title1')
        self.assertEqual(conv.to_python('notslug'), None)
        self.assertEqual(conv.to_python(''), None)
        self.assertEqual(list(conv.options()), [
            ('slug1', 'title1'),
            ('slug2', 'title2'),
            ('slug3', 'title3'),
        ])
