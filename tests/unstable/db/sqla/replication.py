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

    def test_reflect(self):
        # Schema
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
            same = Column(String)
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
            same = Column(String)
        self.create_all()
        # Data for source
        with self.db.begin():
            a1 = A1(id=1, same='s1')
            self.db.add(a1)
        # Test when reflection doesn't exist
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.reflect(a1, A2)
        self.assertNothingChanged(hist)
        self.assertIsNone(a2)
        # Data for target (reflection exists)
        with self.db.begin():
            a2 = A2(id=1, same='s2')
            self.db.add(a2)
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

    def test_replicate_basic(self):
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
        # Test when reflection doesn't exist
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.replicate(a1, A2)
        hist.assert_created_one(A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.id, a1.id)
        self.assertEqual(a2.same, 's1')
        self.assertIsNone(a2.different2)
        # Update data
        with self.db.begin():
            a1.same = 's2'
        # Test when reflection is already loaded
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.replicate(a1, A2)
        hist.assert_updated_one(A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.same, 's2')
        self.assertIsNone(a2.different2)
        # Once more but when reflection is not loaded
        self.db.expunge(a2)
        with self.db.begin():
            a1.same = 's3'
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.replicate(a1, A2)
        hist.assert_updated_one(A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.same, 's3')
        self.assertIsNone(a2.different2)

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

    def test_replicate_m2o(self):
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
        # Data: reflections for both child and parent don't exist
        with self.db.begin():
            p11 = P1(id=1)
            c1 = C1(id=1, parent=p11)
            self.db.add(c1)
        # Test
        with DBHistory(self.db) as hist, self.db.begin():
            c2 = replication.replicate(c1, C2)
        hist.assert_created_one(C2)
        self.assertEqual(len(hist.created), 1)
        self.assertIsNone(c2.parent)
        # Reflection for child already exists and loaded
        self.assertEqual(c1.parent, p11)
        with DBHistory(self.db) as hist, self.db.begin():
            c2 = replication.replicate(c1, C2)
        self.assertIsNone(c2.parent)
        # Reflection for child already exists but not loaded
        self.db.expunge(c2)
        with DBHistory(self.db) as hist, self.db.begin():
            c2 = replication.replicate(c1, C2)
        self.assertIsNone(c2.parent)
        # Reflection parent does exist, but not for child
        with self.db.begin():
            self.db.delete(c2)
            p21 = P2(id=1)
            self.db.add(p21)
        with DBHistory(self.db) as hist, self.db.begin():
            c2 = replication.replicate(c1, C2)
        hist.assert_created_one(C2)
        self.assertEqual(c2.parent, p21)
        # Reflection for child doesn't exist, but not for parent
        with self.db.begin():
            c1.parent = p12 = P1(id=2)
        with DBHistory(self.db) as hist, self.db.begin():
            c2 = replication.replicate(c1, C2)
        hist.assert_updated_one(C2)
        self.assertIsNone(c2.parent)

    def test_replicate_o2m(self):
        # Schema
        class P1(self.Base):
            id = Column(Integer, primary_key=True)
            children = relationship('C1')
        class C1(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(P1.id))
            parent = relationship(P1)
        class P2(self.Base):
            id = Column(Integer, primary_key=True)
            children = relationship('C2')
        class C2(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(P2.id))
            parent = relationship(P2)
        self.create_all()
        # Data: reflections for both child and parent don't exist
        with self.db.begin():
            p1 = P1(id=1, children=[C1(id=1)])
            c2 = C2(id=1)
            self.db.add_all([p1, c2])
        # Reflection for one parent exists
        p2 = replication.replicate(p1, P2)
        # XXX Is this always correct? Should it be always replicated from other
        # side only?
        self.assertEqual(p2.children, [])
