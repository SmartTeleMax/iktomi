import unittest
from sqlalchemy import Column, Integer, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from iktomi.db.sqla.declarative import AutoTableNameMeta
from iktomi.unstable.db.sqla.mixin import declared_mixin


class Tests(unittest.TestCase):

    def setUp(self):
        self.Base = declarative_base(name='Base', metaclass=AutoTableNameMeta)

    def test_short_form(self):
        called = [0]
        @declared_mixin
        def MixIn():
            '''Docstring'''
            called[0] += 1
            id = Column(Integer, primary_key=True)
            data = Column(Integer)
        self.assertIsInstance(MixIn, type)
        self.assertEqual(MixIn.__doc__, 'Docstring')
        class A(self.Base, MixIn): pass
        self.assertEqual(called[0], 1)
        class B(self.Base, MixIn): pass
        self.assertEqual(called[0], 2)
        self.assertIsNot(A.id, B.id)

    def test_with_base(self):
        @declared_mixin
        def PKMixIn():
            id = Column(Integer, primary_key=True)
        @declared_mixin(PKMixIn)
        def PKAndDataMixIn():
            data = Column(Integer)
        class A(self.Base, PKAndDataMixIn): pass
        class B(self.Base, PKAndDataMixIn): pass
        self.assertIsNot(A.id, B.id)
        self.assertIsNot(A.data, B.data)

    def test_reference(self):
        def TreeMixIn(cls):
            @declared_mixin
            def _TreeMixIn():
                id = Column(Integer, primary_key=True)
                parent_id = Column(ForeignKey(id))
                parent = relationship(cls, remote_side=id)
            return _TreeMixIn
        class A(self.Base, TreeMixIn('A')): pass
        class B(self.Base, TreeMixIn('B')): pass
        # XXX What to test here in addition to the fact that it compiles?
