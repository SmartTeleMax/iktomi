import unittest
from sqlalchemy import Column, Integer, String, ForeignKey, \
                       ForeignKeyConstraint, create_engine
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker, relationship, composite, \
                           column_property
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.sql.functions import char_length
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
        hist.assert_nothing_happened()
        self.assertIsNone(a2)
        # Data for target (reflection exists)
        with self.db.begin():
            a2 = A2(id=2, same='s2')
            self.db.add(a2)
        # Test when reflection is already loaded
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.reflect(a1, A2)
        hist.assert_nothing_happened()
        self.assertIsNotNone(a2)
        self.assertEqual(a2.same, 's2')
        # Once more but when reflection is not loaded
        self.db.expunge(a2)
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.reflect(a1, A2)
        hist.assert_nothing_happened()
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
        self.assertEqual(len(hist.created_idents), 1)
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
        assert len(hist.created_idents)==1
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
        self.assertEqual(a2.b, [])
        self.assertEqual(b2.a, [])

    def test_replicate_o2m_private(self):
        # Schema
        class P1(self.Base):
            id = Column(Integer, primary_key=True)
            children = relationship('C1', cascade='all,delete-orphan')
        class C1(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(P1.id), nullable=False)
            parent = relationship(P1)
            data = Column(String)
        class P2(self.Base):
            id = Column(Integer, primary_key=True)
            children = relationship('C2', cascade='all,delete-orphan')
        class C2(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(P2.id), nullable=False)
            parent = relationship(P2)
            data = Column(String)
        self.create_all()
        # Data
        with self.db.begin():
            p1 = P1(id=2, children=[C1(id=2, data='a1')])
            self.db.add(p1)
        # New
        with DBHistory(self.db) as hist, self.db.begin():
            p2 = replication.replicate(p1, P2)
        hist.assert_created_one(P2)
        hist.assert_created_one(C2)
        self.assertEqual(len(p2.children), 1)
        self.assertEqual(p2.children[0].id, 2)
        self.assertEqual(p2.children[0].data, 'a1')
        # Append new child and update existing
        with self.db.begin():
            p1.children[0].data = 'a2'
            p1.children.append(C1(id=4, data='b1'))
        with DBHistory(self.db) as hist, self.db.begin():
            p2 = replication.replicate(p1, P2)
        hist.assert_created_one(C2)
        hist.assert_updated_one(C2)
        self.assertEqual(len(p2.children), 2)
        self.assertEqual(set([(c.id, c.data) for c in p2.children]),
                         set([(2, 'a2'), (4, 'b1')]))
        # Update one and remove other child
        with self.db.begin():
            p1.children = [C1(id=4, data='b2')]
        with DBHistory(self.db) as hist, self.db.begin():
            p2 = replication.replicate(p1, P2)
        self.assertEqual(self.db.query(C2).count(), 1)
        self.assertEqual(len(p2.children), 1)
        self.assertEqual(p2.children[0].id, 4)
        self.assertEqual(p2.children[0].data, 'b2')

    def test_replicate_o2o_private(self):
        # Schema
        class P1(self.Base):
            id = Column(Integer, primary_key=True)
            child = relationship('C1', uselist=False,
                                 cascade='all,delete-orphan')
        class C1(self.Base):
            id = Column(ForeignKey(P1.id), primary_key=True)
            parent = relationship(P1)
            data = Column(String)
        class P2(self.Base):
            id = Column(Integer, primary_key=True)
            child = relationship('C2', uselist=False,
                                 cascade='all,delete-orphan')
        class C2(self.Base):
            id = Column(ForeignKey(P2.id), primary_key=True)
            parent = relationship(P2)
            data = Column(String)
        self.create_all()
        # Data
        with self.db.begin():
            p1 = P1(id=2, child=C1(data='a1'))
            self.db.add(p1)
        # New
        with DBHistory(self.db) as hist, self.db.begin():
            p2 = replication.replicate(p1, P2)
        hist.assert_created_one(P2)
        hist.assert_created_one(C2)
        self.assertIsNotNone(p2.child)
        # Update child
        with self.db.begin():
            p1.child.data = 'a2'
            p2 = replication.replicate(p1, P2)
        self.assertIsNotNone(p2.child)
        self.assertEqual(p2.child.id, 2)
        self.assertEqual(p2.child.data, 'a2')
        # Change child
        with self.db.begin():
            p1.child = C1(data='a3')
            self.db.flush() # XXX Right now fails without this
            p2 = replication.replicate(p1, P2)
        self.assertIsNotNone(p2.child)
        self.assertEqual(p2.child.id, 2)
        self.assertEqual(p2.child.data, 'a3')
        # Remove child (set to None)
        with self.db.begin():
            p1.child = None
            p2 = replication.replicate(p1, P2)
        self.assertIsNone(p2.child)

    def test_replicate_m2m_ordered(self):
        # Schema
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
            data = Column(String)
            _ab = relationship('AB1', order_by='AB1.position',
                               cascade='all,delete-orphan',
                               collection_class=ordering_list('position'))
            b = association_proxy('_ab', 'b', creator=lambda b: AB1(b=b))
        class B1(self.Base):
            id = Column(Integer, primary_key=True)
        class AB1(self.Base):
            a_id = Column(ForeignKey(A1.id), nullable=False, primary_key=True)
            b_id = Column(ForeignKey(B1.id), nullable=False, primary_key=True)
            b = relationship(B1)
            position = Column(Integer, nullable=False)
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
            data = Column(String)
            _ab = relationship('AB2', order_by='AB2.position',
                               cascade='all,delete-orphan',
                               collection_class=ordering_list('position'))
            b = association_proxy('_ab', 'b', creator=lambda b: AB2(b=b))
        class B2(self.Base):
            id = Column(Integer, primary_key=True)
        class AB2(self.Base):
            a_id = Column(ForeignKey(A2.id), nullable=False, primary_key=True)
            b_id = Column(ForeignKey(B2.id), nullable=False, primary_key=True)
            b = relationship(B2)
            position = Column(Integer, nullable=False)
        self.create_all()
        # Data
        with self.db.begin():
            b11 = B1(id=2)
            b12 = B1(id=4)
            a1 = A1(id=2, b=[b11, b12])
            b21 = B2(id=2)
            self.db.add_all([a1, b21])
        # Test with 2 children: one with existing reflection and one without it
        with self.db.begin():
            a2 = replication.replicate(a1, A2)
        self.assertEqual(len(a2.b), 1)
        self.assertEqual(a2.b[0].id, 2)
        # Insert into front
        with self.db.begin():
            b13 = B1(id=6)
            b23 = B2(id=6)
            self.db.add_all([b13, b23])
        with self.db.begin():
            a1.b = [b13, b11]
            a2 = replication.replicate(a1, A2)
        self.assertEqual(len(a2.b), 2)
        self.assertEqual(a2.b[0].id, 6)
        self.assertEqual(a2.b[1].id, 2)
        # Change order
        with self.db.begin():
            a1.b = [b11, b13]
            a2 = replication.replicate(a1, A2)
        self.assertEqual(len(a2.b), 2)
        self.assertEqual(a2.b[0].id, 2)
        self.assertEqual(a2.b[1].id, 6)
        # Remove
        with self.db.begin():
            a1.b = []
            a2 = replication.replicate(a1, A2)
        self.assertEqual(len(a2.b), 0)

    def test_replication_o2m_dict(self):
        # Schema
        class P1(self.Base):
            id = Column(Integer, primary_key=True)
            _children = relationship(
                        'C1', cascade='all,delete-orphan',
                        collection_class=attribute_mapped_collection('key'))
            children = association_proxy(
                        '_children', 'value',
                        creator=lambda k, v: C1(key=k, value=v))
        class C1(self.Base):
            parent_id = Column(ForeignKey(P1.id), nullable=False,
                               primary_key=True)
            parent = relationship(P1)
            key = Column(String(10), nullable=False, primary_key=True)
            value = Column(String)
        class P2(self.Base):
            id = Column(Integer, primary_key=True)
            _children = relationship(
                        'C2', cascade='all,delete-orphan',
                        collection_class=attribute_mapped_collection('key'))
            children = association_proxy(
                        '_children', 'value',
                        creator=lambda k, v: C1(key=k, value=v))
        class C2(self.Base):
            parent_id = Column(ForeignKey(P2.id), nullable=False,
                               primary_key=True)
            parent = relationship(P2)
            key = Column(String(10), nullable=False, primary_key=True)
            value = Column(String)
        self.create_all()
        # Data
        with self.db.begin():
            p1 = P1(children={'k1': 'v11', 'k2': 'v2'})
            self.db.add(p1)
        # New
        with self.db.begin():
            p2 = replication.replicate(p1, P2)
        self.assertEqual(p2.children, {'k1': 'v11', 'k2': 'v2'})
        # Update
        with self.db.begin():
            p1.children['k1'] = 'v12'
            del p1.children['k2']
            p1.children['k3'] = 'v3'
            self.db.flush() # XXX Fails without this
            p2 = replication.replicate(p1, P2)
        self.assertEqual(p2.children, {'k1': 'v12', 'k3': 'v3'})

    def test_replication_m2m_set(self):
        # Schema
        class PC1(self.Base):
            p_id = Column(ForeignKey('P1.id'), primary_key=True)
            c_id = Column(ForeignKey('C1.id'), primary_key=True)
        class P1(self.Base):
            id = Column(Integer, primary_key=True)
            children = relationship('C1', secondary=PC1.__table__,
                                    collection_class=set)
        class C1(self.Base):
            id = Column(Integer, primary_key=True)
        class PC2(self.Base):
            p_id = Column(ForeignKey('P2.id'), primary_key=True)
            c_id = Column(ForeignKey('C2.id'), primary_key=True)
        class P2(self.Base):
            id = Column(Integer, primary_key=True)
            children = relationship('C2', secondary=PC2.__table__,
                                    collection_class=set)
        class C2(self.Base):
            id = Column(Integer, primary_key=True)
        self.create_all()
        # Data
        with self.db.begin():
            c11 = C1(id=2)
            p1 = P1(children=set([c11, C1(id=4)]))
            c21 = C2(id=2)
            self.db.add_all([p1, c21])
        # New: one has reflection and other doesn't
        with self.db.begin():
            p2 = replication.replicate(p1, P2)
        self.assertEqual(p2.children, set([c21]))
        # Update
        with self.db.begin():
            p1.children = set([c11, C1(id=6)])
            c23 = C2(id=6)
            self.db.add(c23)
            p2 = replication.replicate(p1, P2)
        self.assertEqual(p2.children, set([c21, c23]))
        # Empty
        with self.db.begin():
            p1.children = set()
            p2 = replication.replicate(p1, P2)
        self.assertEqual(p2.children, set())

    def test_replicate_m2m_backref(self):
        # Schema
        class AB1(self.Base):
            a_id = Column(ForeignKey('A1.id'), primary_key=True)
            b_id = Column(ForeignKey('B1.id'), primary_key=True)
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
            data = Column(String)
            b = relationship('B1', secondary=AB1.__table__, backref='a')
        class B1(self.Base):
            id = Column(Integer, primary_key=True)
        class AB2(self.Base):
            a_id = Column(ForeignKey('A2.id'), primary_key=True)
            b_id = Column(ForeignKey('B2.id'), primary_key=True)
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
            data = Column(String)
            b = relationship('B2', secondary=AB2.__table__, backref='a')
        class B2(self.Base):
            id = Column(Integer, primary_key=True)
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
        self.assertEqual(a2.b, [])
        self.assertEqual(b2.a, [])

    def test_replicate_declared_attr(self):
        # Schema
        class Common(object):
            @declared_attr
            def id(cls):
                return Column(Integer, primary_key=True)
            @declared_attr
            def same(cls):
                return Column(String)
        class A1(self.Base, Common):
            pass
        class A2(self.Base, Common):
            pass
        self.create_all()
        # Data
        with self.db.begin():
            a1 = A1(id=2, same='s')
            self.db.add(a1)
        # Test when reflection doesn't exist
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.replicate(a1, A2)
        hist.assert_created_one(A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.id, a1.id)
        self.assertEqual(a2.same, 's')

    def test_replicate_self_reference(self):
        # Schema
        class N1(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(id))
            parent = relationship('N1', remote_side=id, backref='children')
        class N2(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(id))
            parent = relationship('N2', remote_side=id, backref='children')
        self.create_all()
        # Data
        with self.db.begin():
            n12 = N1(id=4)
            n11 = N1(id=2, children=[n12])
            n22 = N2(id=4)
            self.db.add_all([n11, n22])
        # Test new
        with self.db.begin():
            n22 = replication.replicate(n12, N2)
        self.assertIsNotNone(n22)
        self.assertEqual(n22.children, [])
        self.assertIsNone(n22.parent)
        # Now we have child, but it shouldn't be replicated via children attr
        with self.db.begin():
            n21 = replication.replicate(n11, N2)
        self.assertIsNotNone(n21)
        self.assertEqual(n22.children, [])
        self.assertIsNone(n22.parent)
        # Now with existing reflection for parent
        with self.db.begin():
            n22 = replication.replicate(n12, N2)
        self.assertEqual(n21.children, [n22])
        self.assertEqual(n22.parent, n21)

    def test_include_exclude_relationship(self):
        # Schema
        class N1(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(id))
            parent = relationship('N1', remote_side=id, backref='children')
        replication.exclude(N1.parent)
        replication.include(N1.children)
        class N2(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(id))
            parent = relationship('N2', remote_side=id, backref='children')
        self.create_all()
        # Data
        with self.db.begin():
            n12 = N1(id=4)
            n11 = N1(id=2, children=[n12, N1(id=6)])
            n22 = N2(id=4)
            self.db.add_all([n11, n22])
        # Test new (reflection of one child exists)
        with self.db.begin():
            n21 = replication.replicate(n11, N2)
        self.assertIsNotNone(n21)
        self.assertEqual(n21.children, [n22])
        self.assertIsNotNone(n22.parent)
        # Check that parent is not replicated
        with self.db.begin():
            n22.parent = None
        with self.db.begin():
            n22 = replication.replicate(n12, N2)
        self.assertIsNotNone(n12.parent)
        self.assertIsNone(n22.parent)
        self.assertEqual(n21.children, [])

    def test_exclude_column(self):
        # Schema
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
            data = Column(String)
            replication.exclude(data)
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
            data = Column(String)
        self.create_all()
        # Data
        with self.db.begin():
            a1 = A1(id=2, data='a')
            self.db.add(a1)
        # Test
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.replicate(a1, A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.id, a1.id)
        self.assertIsNone(a2.data)

    def test_replication_composite(self):
        # Schema
        class Point(object):
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def __composite_values__(self):
                return self.x, self.y
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
            point = composite(Point,
                              Column('point_x', Integer, nullable=False),
                              Column('point_y', Integer, nullable=False))
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
            point = composite(Point,
                              Column('point_x', Integer, nullable=False),
                              Column('point_y', Integer, nullable=False))
        self.create_all()
        # Data
        with self.db.begin():
            a1 = A1(point=Point(1, 2))
            self.db.add(a1)
        # Test
        with self.db.begin():
            a2 = replication.replicate(a1, A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a1.point.x, 1)
        self.assertEqual(a1.point.y, 2)

    def test_replication_composite_pk_relationship(self):
        # Schema
        class Category1(self.Base):
            id = Column(Integer, primary_key=True)
        class Node1(self.Base):
            id = Column(Integer, primary_key=True)
            category_id = Column(ForeignKey(Category1.id), nullable=False)
            category = relationship(Category1)
            parent_id = Column(Integer)
            parent = relationship('Node1', remote_side=id)
            __table_args__ = (
                ForeignKeyConstraint([parent_id, category_id],
                                     [id, category_id]),
            )
        class Category2(self.Base):
            id = Column(Integer, primary_key=True)
        class Node2(self.Base):
            id = Column(Integer, primary_key=True)
            category_id = Column(ForeignKey(Category2.id), nullable=False)
            category = relationship(Category2)
            parent_id = Column(Integer)
            parent = relationship('Node2', remote_side=id)
            __table_args__ = (
                ForeignKeyConstraint([parent_id, category_id],
                                     [id, category_id]),
            )
        self.create_all()
        # Data
        with self.db.begin():
            category1 = Category1(id=2)
            node11 = Node1(id=2, category=category1)
            node12 = Node1(id=4, category=category1, parent=node11)
            category2 = Category2(id=2)
            node21 = Node2(id=2, category=category2)
            self.db.add_all([node12, node21])
        self.assertEqual(node12.parent, node11)
        # Test
        with self.db.begin():
            node22 = replication.replicate(node12, Node2)
        self.assertIsNotNone(node22)
        self.assertEqual(node22.parent, node21)

    def test_replication_shared_parent(self):
        # Schema
        class P(self.Base):
            id = Column(Integer, primary_key=True)
        class C1(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(P.id))
            parent = relationship(P)
        class C2(self.Base):
            id = Column(Integer, primary_key=True)
            parent_id = Column(ForeignKey(P.id))
            parent = relationship(P)
        self.create_all()
        # Data
        with self.db.begin():
            p = P(id=2)
            c1 = C1(id=2, parent=p)
            self.db.add(c1)
        # Test
        with self.db.begin():
            c2 = replication.replicate(c1, C2)
        self.assertIsNotNone(c2)
        self.assertIs(c2.parent, p)
        with self.db.begin():
            c1.parent = None
            c2 = replication.replicate(c1, C2)
        self.assertIsNone(c2.parent)

    def test_replicate_circular(self):
        # Schema
        class P1(self.Base):
            id = Column(Integer, primary_key=True)
            data = Column(String)
        class C1(self.Base):
            id = Column(ForeignKey(P1.id), primary_key=True,
                        autoincrement=False)
            more = Column(String)
            parent = relationship(P1, cascade='all,delete-orphan',
                                  single_parent=True)
            replication.include(parent)
        P1.child = relationship(C1, uselist=False, cascade='all,delete-orphan')
        class P2(self.Base):
            id = Column(Integer, primary_key=True)
            data = Column(String)
        class C2(self.Base):
            id = Column(ForeignKey(P2.id), primary_key=True,
                        autoincrement=False)
            more = Column(String)
            parent = relationship(P2, cascade='all,delete-orphan',
                                  single_parent=True)
        P2.child = relationship(C2, uselist=False, cascade='all,delete-orphan')
        self.create_all()
        # Data
        with self.db.begin():
            p1 = P1(id=2, data='a', child=C1(more='b'))
            self.db.add(p1)
        # Test
        with self.db.begin():
            p2 = replication.replicate(p1, P2)
        self.assertIsNotNone(p2)
        self.assertEqual(p2.id, 2)
        self.assertIsNotNone(p2.child)
        self.assertEqual(p2.child.id, 2)
        self.assertEqual(p2.data, 'a')
        self.assertEqual(p2.child.more, 'b')

    def test_replication_viewonly(self):
        # Schema
        class AB1(self.Base):
            a_id = Column(ForeignKey('A1.id'), primary_key=True)
            b_id = Column(ForeignKey('B1.id'), primary_key=True)
        class B1(self.Base):
            id = Column(Integer, primary_key=True)
            value = Column(Integer, nullable=False)
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
            b = relationship(B1, secondary=AB1.__table__,
                             secondaryjoin=((AB1.b_id==B1.id) & (B1.value>0)),
                             viewonly=True)
        class AB2(self.Base):
            a_id = Column(ForeignKey('A2.id'), primary_key=True)
            b_id = Column(ForeignKey('B2.id'), primary_key=True)
        class B2(self.Base):
            id = Column(Integer, primary_key=True)
            value = Column(Integer, nullable=False)
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
            b = relationship(B2, secondary=AB2.__table__,
                             secondaryjoin=((AB2.b_id==B2.id) & (B2.value>0)),
                             viewonly=True)
        self.create_all()
        # Data
        with self.db.begin():
            a1 = A1(id=2)
            b1 = B1(id=2, value=1)
            ab1 = AB1(a_id=2, b_id=2)
            self.db.add_all([a1, b1, ab1])
            b2 = B2(id=2, value=1)
        self.assertEqual(a1.b, [b1])
        # Test
        with self.db.begin():
            a2 = replication.replicate(a1, A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.b, [])

    def test_replication_dynamic(self):
        # Schema
        class AB1(self.Base):
            a_id = Column(ForeignKey('A1.id'), primary_key=True)
            b_id = Column(ForeignKey('B1.id'), primary_key=True)
        class B1(self.Base):
            id = Column(Integer, primary_key=True)
            a = relationship('A1', secondary=AB1.__table__)
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
            b = relationship(B1, secondary=AB1.__table__, lazy='dynamic')
        class AB2(self.Base):
            a_id = Column(ForeignKey('A2.id'), primary_key=True)
            b_id = Column(ForeignKey('B2.id'), primary_key=True)
        class B2(self.Base):
            id = Column(Integer, primary_key=True)
            a = relationship('A2', secondary=AB2.__table__)
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
            b = relationship(B2, secondary=AB2.__table__, lazy='dynamic')
        self.create_all()
        # Data
        with self.db.begin():
            b1 = B1(id=2)
            a1 = A1(id=2, b=[b1])
            b2 = B2(id=2)
            self.db.add_all([a1, b2])
        # Test from dynamic side
        with self.db.begin():
            a2 = replication.replicate(a1, A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.b.all(), [])
        # Test from oposite side
        with self.db.begin():
            b2 = replication.replicate(b1, B2)
        self.assertIsNotNone(b2)
        self.assertEqual(b2.a, [a2])
        self.assertEqual(a2.b.all(), [b2])

    def test_replication_single_table_slices(self):
        # Schema
        class C1(self.Base):
            id = Column(Integer, primary_key=True)
        class C1LangA(C1):
            __tablename__ = None
            data = Column('data_a', String)
        class C1LangB(C1):
            __tablename__ = None
            data = Column('data_b', String)
        class C2(self.Base):
            id = Column(Integer, primary_key=True)
        class C2LangA(C2):
            __tablename__ = None
            data = Column('data_a', String)
        class C2LangB(C2):
            __tablename__ = None
            data = Column('data_b', String)
        self.create_all()
        # Data
        with self.db.begin():
            c1_a = C1LangA(id=2, data='a')
            self.db.add(c1_a)
        with self.db.begin():
            c1_b = self.db.query(C1LangB).get(2)
            self.assertIsNone(c1_b.data)
            c1_b.data = 'b'
        # Test
        with self.db.begin():
            c2_a = replication.replicate(c1_a, C2LangA)
        self.assertIsNotNone(c2_a)
        self.assertEqual(c2_a.id, 2)
        self.assertEqual(c2_a.data, 'a')
        c2_b = self.db.query(C2LangB).get(2)
        self.assertIsNone(c2_b.data)

    def test_replicate_expression_property(self):
        # Schema
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
            data = Column(String)
            expr = column_property(data+' '+data)
            func = column_property(char_length(data))
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
            data = Column(String)
            expr = column_property(data+' '+data)
            func = column_property(char_length(data))
        self.create_all()
        # Data
        with self.db.begin():
            a1 = A1(id=2, data='aaa')
            self.db.add(a1)
        self.assertEqual(a1.expr, 'aaa aaa')
        self.assertEqual(a1.func, 3)
        # Test when reflection doesn't exist
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.replicate(a1, A2)
        hist.assert_created_one(A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.data, 'aaa')
        self.assertEqual(a2.expr, 'aaa aaa')
        self.assertEqual(a2.func, 3)
        # Update data
        with self.db.begin():
            a1.data = 'aaaaa'
        # Test when reflection is already loaded
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.replicate(a1, A2)
        hist.assert_updated_one(A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.data, 'aaaaa')
        self.assertEqual(a2.expr, 'aaaaa aaaaa')
        self.assertEqual(a2.func, 5)

    def test_ordering_list_duplicate_reference(self):
        # Schema
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
            bs = relationship('B1', order_by='B1.position',
                               cascade='all,delete-orphan',
                               collection_class=ordering_list('position'))
        class C1(self.Base):
            id = Column(Integer, primary_key=True)
        class B1(self.Base):
            a_id = Column(ForeignKey(A1.id), nullable=False, primary_key=True)
            position = Column(Integer, nullable=False, primary_key=True)
            c_id = Column(ForeignKey(C1.id), nullable=False)
            c = relationship(C1)
            data = Column(String)
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
            bs = relationship('B2', order_by='B2.position',
                               cascade='all,delete-orphan',
                               collection_class=ordering_list('position'))
        class C2(self.Base):
            id = Column(Integer, primary_key=True)
        class B2(self.Base):
            a_id = Column(ForeignKey(A2.id), nullable=False, primary_key=True)
            position = Column(Integer, nullable=False, primary_key=True)
            c_id = Column(ForeignKey(C2.id), nullable=False)
            c = relationship(C2)
            data = Column(String)
        self.create_all()
        # Data
        with self.db.begin():
            c1 = C1(id=1)
            self.db.add(c1)
            c2 = replication.replicate(c1, C2)
        with self.db.begin():
            a1 = A1(bs=[B1(c=c1, data='a'), B1(c=c1, data='b')])
            self.db.add(a1)
        # Test when reflection doesn't exist
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.replicate(a1, A2)
        hist.assert_created_one(A2)
        self.assertEqual(len(a2.bs), 2)
        self.assertEqual(a2.bs[0].data, 'a')
        self.assertEqual(a2.bs[1].data, 'b')
        self.assertIs(a2.bs[0].c, c2)
        self.assertIs(a2.bs[1].c, c2)
        # Test when reflection exists
        with DBHistory(self.db) as hist, self.db.begin():
            a1.bs += [B1(c=c1, data='c')]
            a2 = replication.replicate(a1, A2)
        hist.assert_created_one(B2)
        self.assertEqual(len(a2.bs), 3)
        self.assertEqual(a2.bs[0].data, 'a')
        self.assertEqual(a2.bs[1].data, 'b')
        self.assertEqual(a2.bs[2].data, 'c')
        self.assertIs(a2.bs[0].c, c2)
        self.assertIs(a2.bs[1].c, c2)
        self.assertIs(a2.bs[2].c, c2)
