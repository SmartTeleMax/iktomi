# -*- coding: utf-8 -*-
import unittest
from iktomi.db.sqla.types import StringList, IntegerList,\
    Html, HtmlString, HtmlText
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import Session
from jinja2 import Markup
import re


Base = declarative_base()


class CustomMarkup(Markup):

    def __init__(self, value):
        # removing multiple spaces for test purposes
        self.markup = Markup(re.sub("\s+", " ", value))

    def __eq__(self, other):
        return self.markup == other


class TypesObject(Base):
    __tablename__ = 'TypesObject'

    id = Column(Integer, primary_key=True)
    words = Column(StringList(100))
    numbers = Column(IntegerList(100))
    html_string1 = Column(Html(String(100)))
    html_string2 = Column(HtmlString(100))
    html_text = Column(HtmlText)
    html_custom = Column(Html(String, markup_class=CustomMarkup))


class Markupable(object):

    def __init__(self, value):
        self.value = value

    def __html__(self):
        return self.value

    def __unicode__(self):
        return self.value


class TypeDecoratorsTest(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(bind=self.engine)

    def tearDown(self):
        self.db.query(TypesObject).delete()
        self.db.commit()
        self.db.close()

    def test_string_list(self):
        words = ['one', 'two', 'three', 'four', 'five']
        obj = TypesObject()
        obj.words = words
        self.db.add(obj)
        self.db.commit()

        self.db.close()
        self.db = Session(bind=self.engine)
        obj = self.db.query(TypesObject).first()
        self.assertEqual(words, obj.words)

    def test_integer_list(self):
        numbers = [1, 5, 10, 15, 20]
        obj = TypesObject()
        obj.numbers = numbers
        self.db.add(obj)
        self.db.commit()

        self.db.close()
        self.db = Session(bind=self.engine)
        obj = self.db.query(TypesObject).first()
        self.assertEqual(numbers, obj.numbers)

    def test_string_wrapped_in_html(self):
        obj = TypesObject()
        obj.html_string1 = Markupable('<html>value</html>')
        self.db.add(obj)
        self.db.commit()
        self.db.close()

        self.db = Session(bind=self.engine)
        obj = self.db.query(TypesObject).first()
        self.assertIsInstance(obj.html_string1, Markup)
        self.assertEqual('<html>value</html>', obj.html_string1)

    def test_html_string(self):
        obj = TypesObject()
        obj.html_string2 = Markupable('<html>value</html>')
        self.db.add(obj)
        self.db.commit()
        self.db.close()

        self.db = Session(bind=self.engine)
        obj = self.db.query(TypesObject).first()
        self.assertIsInstance(obj.html_string2, Markup)
        self.assertEqual('<html>value</html>', obj.html_string2)

    def test_html_text(self):
        obj = TypesObject()
        text = "<html>" + "the sample_text " * 100 + "</html>"
        obj.html_text = Markupable(text)
        self.db.add(obj)
        self.db.commit()
        self.db.close()

        self.db = Session(bind=self.engine)
        obj = self.db.query(TypesObject).first()
        self.assertIsInstance(obj.html_text, Markup)
        self.assertEqual(text, obj.html_text)

    def test_html_custom_markup(self):
        obj = TypesObject()
        obj.html_custom = Markupable('<html>   value   </html>')
        self.db.add(obj)
        self.db.commit()
        self.db.close()

        self.db = Session(bind=self.engine)
        obj = self.db.query(TypesObject).first()
        self.assertIsInstance(obj.html_custom, CustomMarkup)
        self.assertEqual('<html> value </html>', obj.html_custom)

