import unittest
from sqlalchemy import Column, Integer, ForeignKey, \
                       PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SAWarning
from iktomi.db.sqla.declarative import AutoTableNameMeta, TableArgsMeta

import warnings
# sqlalchemy/sql/schema.py:496: SAWarning:
# Can't validate argument 'dialect2_b';
# can't locate any SQLAlchemy dialect named 'dialect2'
warnings.filterwarnings('ignore', "can't validate argument", SAWarning)


class AutoTableNameTest(unittest.TestCase):

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
        class D(A):
            __table__ = A.__table__
        self.assertEqual(A.__table__.name, 'A')
        self.assertIs(B.__table__, A.__table__)
        self.assertIs(C.__table__, A.__table__)
        self.assertIs(D.__table__, A.__table__)


class TableArgsTest(unittest.TestCase):

    def test_basic(self):
        args = {'dialect1_a': 1, 'dialect2_b': 2}
        Base = declarative_base(name='Base', metaclass=TableArgsMeta(args))
        class A(Base):
            __tablename__ = 'A'
            id = Column(Integer, primary_key=True)
        self.assertEqual(A.__table_args__, args)

    def test_update(self):
        args = {'dialect1_a': 11, 'dialect2_b': 12}
        Base = declarative_base(name='Base', metaclass=TableArgsMeta(args))
        class A(Base):
            __tablename__ = 'A'
            __table_args__ = {
                'dialect2_b': 22,
                'dialect3_c': 23,
            }
            id = Column(Integer, primary_key=True)
        self.assertEqual(A.__table_args__, {'dialect1_a': 11,
                                            'dialect2_b': 22,
                                            'dialect3_c': 23})

    def test_positional(self):
        args = {'dialect1_a': 11, 'dialect2_b': 12}
        Base = declarative_base(name='Base', metaclass=TableArgsMeta(args))
        class A(Base):
            __tablename__ = 'A'
            id = Column(Integer)
            data = Column(Integer)
            __table_args__ = (
                PrimaryKeyConstraint(id),
                UniqueConstraint(data),
            )
        self.assertEqual(len(A.__table_args__), 3)
        self.assertIsInstance(A.__table_args__[0], PrimaryKeyConstraint)
        self.assertIsInstance(A.__table_args__[1], UniqueConstraint)
        self.assertEqual(A.__table_args__[2], args)
        class B(Base):
            __tablename__ = 'B'
            id = Column(Integer, primary_key=True)
            data = Column(Integer)
            __table_args__ = (
                PrimaryKeyConstraint(id),
                UniqueConstraint(id),
                {'dialect2_b': 22,
                 'dialect3_c': 23},
            )
        self.assertEqual(len(B.__table_args__), 3)
        self.assertIsInstance(B.__table_args__[0], PrimaryKeyConstraint)
        self.assertIsInstance(B.__table_args__[1], UniqueConstraint)
        self.assertEqual(B.__table_args__[2], {'dialect1_a': 11,
                                               'dialect2_b': 22,
                                               'dialect3_c': 23})
