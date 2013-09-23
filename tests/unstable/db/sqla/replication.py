import unittest
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from testalchemy import DBHistory
from iktomi.db.sqla.declarative import AutoTableNameMeta
from iktomi.unstable.db.sqla import replication


# Notes for test authors:
# 1. Always use even numbers for id. In this case any bug with missing id value
# (or None) will cause creation of new object with next odd id that is easy to
# catch.


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
            a1 = A1(id=2, same='s1')
            self.db.add(a1)
        # Test when reflection doesn't exist
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.reflect(a1, A2)
        self.assertNothingChanged(hist)
        self.assertIsNone(a2)
        # Data for target (reflection exists)
        with self.db.begin():
            a2 = A2(id=2, same='s2')
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
            a1 = A1(id=2, same='s1', different1='d1')
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
        self.assertEqual(a2.id, a1.id)
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
        self.assertEqual(a2.id, a1.id)
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
            a1 = A1(id=2, name='n')
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
            p11 = P1(id=2)
            c1 = C1(id=2, parent=p11)
            self.db.add(c1)
        # Test
        with DBHistory(self.db) as hist, self.db.begin():
            c2 = replication.replicate(c1, C2)
        hist.assert_created_one(C2)
        self.assertEqual(len(hist.created), 1)
        self.assertEqual(c2.id, c1.id)
        self.assertIsNone(c2.parent)
        # Reflection for child already exists and loaded
        self.assertEqual(c1.parent, p11)
        with DBHistory(self.db) as hist, self.db.begin():
            c2 = replication.replicate(c1, C2)
        self.assertEqual(c2.id, c1.id)
        self.assertIsNone(c2.parent)
        # Reflection for child already exists but not loaded
        self.db.expunge(c2)
        with DBHistory(self.db) as hist, self.db.begin():
            c2 = replication.replicate(c1, C2)
        self.assertEqual(c2.id, c1.id)
        self.assertIsNone(c2.parent)
        # Reflection parent does exist, but not for child
        with self.db.begin():
            self.db.delete(c2)
            p21 = P2(id=2)
            self.db.add(p21)
        with DBHistory(self.db) as hist, self.db.begin():
            c2 = replication.replicate(c1, C2)
        hist.assert_created_one(C2)
        self.assertEqual(c2.id, c1.id)
        self.assertEqual(c2.parent, p21)
        # Reflection for child doesn't exist, but not for parent
        with self.db.begin():
            c1.parent = p12 = P1(id=4)
        with DBHistory(self.db) as hist, self.db.begin():
            c2 = replication.replicate(c1, C2)
        hist.assert_updated_one(C2)
        self.assertEqual(c2.id, c1.id)
        self.assertIsNone(c2.parent)
        # Replicate when relation is None
        with self.db.begin():
            c1.parent = None
            c2 = replication.replicate(c1, C2)
        self.assertIsNone(c2.parent)

    @unittest.skip
    # XXX Temporary disabled till we find proper algorithm to determine
    # relationship columns that should be excluded.
    def test_replicate_relationship_over_column(self):
        # Schema
        # Names of FK column and relationship in CB* are swapped compared to
        # CA* so that in one of them relationship comes before column in
        # dict.keys(): SQLAlchemy uses dict to store attributes so the order is
        # not fixed, but we can try both orders.
        class P1(self.Base):
            id = Column(Integer, primary_key=True)
        class CA1(self.Base):
            id = Column(Integer, primary_key=True)
            a = Column(ForeignKey(P1.id))
            b = relationship(P1)
        class CB1(self.Base):
            id = Column(Integer, primary_key=True)
            b = Column(ForeignKey(P1.id))
            a = relationship(P1)
        class P2(self.Base):
            id = Column(Integer, primary_key=True)
        class CA2(self.Base):
            id = Column(Integer, primary_key=True)
            a = Column(ForeignKey(P2.id))
            b = relationship(P2)
        class CB2(self.Base):
            id = Column(Integer, primary_key=True)
            b = Column(ForeignKey(P2.id))
            a = relationship(P2)
        self.create_all()
        # Data
        with self.db.begin():
            p1 = P1(id=2)
            ca1 = CA1(id=2, b=p1)
            cb1 = CB1(id=2, a=p1)
            self.db.add_all([ca1, cb1])
        # Test: one them will fail if this case is not handled specially.
        with self.db.begin():
            ca2 = replication.replicate(ca1, CA2)
            cb2 = replication.replicate(cb1, CB2)
        self.assertIsNone(ca2.a)
        self.assertIsNone(cb2.b)

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
            p1 = P1(id=2, children=[C1(id=2)])
            c2 = C2(id=2)
            self.db.add_all([p1, c2])
        # Reflection for one parent exists
        with self.db.begin():
            p2 = replication.replicate(p1, P2)
        self.assertEqual(p2.id, p1.id)
        self.assertEqual(p2.children, [])

    def test_replicate_o2o(self):
        # Schema
        class P1(self.Base):
            id = Column(Integer, primary_key=True)
            child = relationship('C1', uselist=False)
        class C1(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(P1.id), unique=True)
            parent = relationship(P1)
        class P2(self.Base):
            id = Column(Integer, primary_key=True)
            child = relationship('C2', uselist=False)
        class C2(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(P2.id), unique=True)
            parent = relationship(P2)
        self.create_all()
        # Data: reflections for both child and parent don't exist
        with self.db.begin():
            c1 = C1(id=2)
            p1 = P1(id=2, child=c1)
            c2 = C2(id=2)
            self.db.add_all([p1, c2])
        # Reflection for one parent exists, property is not reflected for this
        # direction
        with DBHistory(self.db) as hist, self.db.begin():
            p2 = replication.replicate(p1, P2)
        hist.assert_created_one(P2)
        assert len(hist.created)==1
        self.assertEqual(p2.id, p1.id)
        self.assertIsNone(p2.child)
        # Replication from other side, property is reflected
        with DBHistory(self.db) as hist, self.db.begin():
            c2r = replication.replicate(c1, C2)
        hist.assert_updated_one(C2)
        self.assertIs(c2r, c2)
        self.assertIs(c2.parent, p2)

    def test_replicate_m2m(self):
        # Schema
        class AB1(self.Base):
            a_id = Column(ForeignKey('A1.id'), primary_key=True)
            b_id = Column(ForeignKey('B1.id'), primary_key=True)
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
            data = Column(String)
            b = relationship('B1', secondary=AB1.__table__)
        class B1(self.Base):
            id = Column(Integer, primary_key=True)
            a = relationship('A1', secondary=AB1.__table__)
        class AB2(self.Base):
            a_id = Column(ForeignKey('A2.id'), primary_key=True)
            b_id = Column(ForeignKey('B2.id'), primary_key=True)
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
            data = Column(String)
            b = relationship('B2', secondary=AB2.__table__)
        class B2(self.Base):
            id = Column(Integer, primary_key=True)
            a = relationship('A2', secondary=AB2.__table__)
        self.create_all()
        # Data
        with self.db.begin():
            a1 = A1(id=2, data='a1')
            b1 = B1(id=2, a=[a1])
            self.db.add_all([a1, b1])
        # Reflections of both objects don't exist
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.replicate(a1, A2)
        hist.assert_created_one(A2)
        self.assertEqual(a2.id, a1.id)
        self.assertEqual(a2.b, [])
        # Only reflection of replicated object exists
        with DBHistory(self.db) as hist, self.db.begin():
            b2 = replication.replicate(b1, B2)
        hist.assert_created_one(B2)
        self.assertEqual(b2.id, b1.id)
        self.assertEqual(b2.a, [a2])
        self.assertEqual(a2.b, [b2])
        # Verify that related objects are not updated
        with self.db.begin():
            a1.data = 'a2'
            b2 = replication.replicate(b1, B2)
        self.assertEqual(b2.id, b1.id)
        self.assertEqual(b2.a, [a2])
        self.assertEqual(a2.data, 'a1')
        # Removal
        with self.db.begin():
            a1.b = []
            a2 = replication.replicate(a1, A2)
        self.assertEqual(a2.id, a1.id)
        #import pdb; pdb.set_trace()
        self.assertEqual(a2.b, [])
        self.assertEqual(b2.a, [])