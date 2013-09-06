import unittest
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from iktomi.db.sqla.declarative import AutoTableNameMeta, TableArgsMeta


class AutoTableNameText(unittest.TestCase):

    def setUp(self):
        self.Base = declarative_base(name='Base', metaclass=AutoTableNameMeta)

    def test_basic(self):
        class A(self.Base):
            id = Column(Integer, primary_key=True)
        self.assertEqual(A.__tablename__, 'A')
        self.assertEqual(A.__table__.name, 'A')

    def test_explicit(self):
        class A(self.Base):
            __tablename__ = 'B'
            id = Column(Integer, primary_key=True)
        self.assertEqual(A.__tablename__, 'B')
        self.assertEqual(A.__table__.name, 'B')

    def test_inheritance(self):
        class A(self.Base):
            id = Column(Integer, primary_key=True)
        class B(A):
            id = Column(ForeignKey(A.id), primary_key=True)
        class C(B):
            id = Column(ForeignKey(B.id), primary_key=True)
        class D(A):
            id = Column(ForeignKey(A.id), primary_key=True)
        self.assertEqual(B.__table__.name, 'B')
        self.assertEqual(C.__table__.name, 'C')
        self.assertEqual(D.__table__.name, 'D')

    def test_abstract(self):
        class A(self.Base):
            __abstract__ = True
            id = Column(Integer, primary_key=True)
        class B(A):
            pass
        self.assertIsNone(getattr(A, '__table__', None))
        self.assertEqual(B.__table__.name, 'B')

    def test_single_table_inheritance(self):
        class A(self.Base):
            id = Column(Integer, primary_key=True)
        class B(A):
            __tablename__ = None
        class C(A):
            __tablename__ = 'A'
        self.assertEqual(A.__table__.name, 'A')
        self.assertIs(B.__table__, A.__table__)
        self.assertIs(C.__table__, A.__table__)
