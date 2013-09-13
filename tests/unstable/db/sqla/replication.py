import unittest
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from testalchemy import DBHistory
from iktomi.db.sqla.declarative import AutoTableNameMeta
from iktomi.unstable.db.sqla import replication


class ReplicationTests(unittest.TestCase):

    def setUp(self):
        engine = create_engine('sqlite://')
        self.Base = declarative_base(name='Base', metaclass=AutoTableNameMeta,
                                     bind=engine)
        self.db = sessionmaker(autocommit=True)()

    def create_all(self):
        self.Base.metadata.create_all()

    def assertNothingChanged(self, hist):
        map(self.assertFalse, [hist.created, hist.deleted, hist.updated])

    def test_reflect_new(self):
        '''Test `reflect()` when reflection doesn't exist'''
        # Schema
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
        self.create_all()
        # Data
        with self.db.begin():
            a1 = A1()
            self.db.add(a1)
        # Test
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.reflect(a1, A2)
        self.assertNothingChanged(hist)
        self.assertIsNone(a2)

    def test_reflect_existing(self):
        '''Test `reflect()` when reflection already exists, insure attributes
        are not copied'''
        # Schema
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
            same = Column(String)
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
            same = Column(String)
        self.create_all()
        # Data
        with self.db.begin():
            a1 = A1(id=1, same='s1')
            a2 = A2(id=1, same='s2')
            self.db.add_all([a1, a2])
        # Test when reflection is already loaded
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.reflect(a1, A2)
        self.assertNothingChanged(hist)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.same, 's2')
        # Once more but when reflection is not loaded
        self.db.expunge(a2)
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.reflect(a1, A2)
        self.assertNothingChanged(hist)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.same, 's2')

    def test_replicate_basic_new(self):
        # Schema
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
            same = Column(String)
            different1 = Column(String)
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
            same = Column(String)
            different2 = Column(String)
        self.create_all()
        # Data
        with self.db.begin():
            a1 = A1(id=1, same='s1', different1='d1')
            self.db.add(a1)
        # Test
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.replicate(a1, A2)
        hist.assert_created_one(A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.id, a1.id)
        self.assertEqual(a2.same, 's1')
        self.assertIsNone(a2.different2)

    def test_replicate_basic_existing(self):
        # Schema
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
            same = Column(String)
            different1 = Column(String)
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
            same = Column(String)
            different2 = Column(String)
        self.create_all()
        # Data
        with self.db.begin():
            a1 = A1(id=1, same='s11', different1='d1')
            a2 = A2(id=1, same='s2', different2='d2')
            self.db.add_all([a1, a2])
        # Test when reflection is already loaded
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.replicate(a1, A2)
        hist.assert_updated_one(A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.same, 's11')
        self.assertEqual(a2.different2, 'd2')
        # Once more but when reflection is not loaded
        self.db.expunge(a2)
        with self.db.begin():
            a1.same = 's12'
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.replicate(a1, A2)
        hist.assert_updated_one(A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.same, 's12')
        self.assertEqual(a2.different2, 'd2')

    def test_replicate_renamed(self):
        '''Test replication when name of attribute is not equal to the name of
        column (but they are the same in both source and target classes,
        otherwise result is undefined)'''
        # Schema
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
            name = Column('other_name', String)
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
            name = Column('other_name', String)
        self.create_all()
        # Data
        with self.db.begin():
            a1 = A1(id=1, name='n')
            self.db.add(a1)
        # Test
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.replicate(a1, A2)
        hist.assert_created_one(A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.id, a1.id)
        self.assertEqual(a2.name, 'n')

    def test_replicate_new_m2o_missing_parent(self):
        # Schema
        class P1(self.Base):
            id = Column(Integer, primary_key=True)
        class C1(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(P1.id))
            parent = relationship(P1)
        class P2(self.Base):
            id = Column(Integer, primary_key=True)
        class C2(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(P2.id))
            parent = relationship(P2)
        self.create_all()
        # Data
        with self.db.begin():
            c1 = C1(id=1, parent=P1())
            self.db.add(c1)
        # Test
        with DBHistory(self.db) as hist, self.db.begin():
            c2 = replication.replicate(c1, C2)
        hist.assert_created_one(C2)
        self.assertEqual(len(hist.created), 1)
        self.assertIsNone(c2.parent)

    def test_replicate_new_m2o_existing_parent(self):
        # Schema
        class P1(self.Base):
            id = Column(Integer, primary_key=True)
        class C1(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(P1.id))
            parent = relationship(P1)
        class P2(self.Base):
            id = Column(Integer, primary_key=True)
        class C2(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(P2.id))
            parent = relationship(P2)
        self.create_all()
        # Data
        with self.db.begin():
            p1 = P1(id=1)
            c1 = C1(id=1, parent=p1)
            p2 = P2(id=1)
            self.db.add_all([c1, p2])
        # Test when reflection of parent is already loaded
        with DBHistory(self.db) as hist, self.db.begin():
            c2 = replication.replicate(c1, C2)
        hist.assert_created_one(C2)
        self.assertEqual(len(hist.created), 1)
        self.assertIs(c2.parent, p2)
        # Test setting to None
        with self.db.begin():
            c1.parent = None
        with DBHistory(self.db) as hist, self.db.begin():
            c2 = replication.replicate(c1, C2)
        hist.assert_updated_one(C2)
        self.assertIsNone(c2.parent)
        # Once more but when reflection of parent is not loaded
        self.db.expunge(p2)
        with self.db.begin():
            c1.parent = p1
        with DBHistory(self.db) as hist, self.db.begin():
            c2 = replication.replicate(c1, C2)
        hist.assert_updated_one(C2)
        self.assertIsNotNone(c2.parent)
        self.assertIs(c2.parent.id, 1)
