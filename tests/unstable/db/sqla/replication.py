import unittest
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker
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

    def test_basic(self):
        class A1(self.Base):
            id = Column(Integer, primary_key=True)
            same = Column(String)
            different1 = Column(String)
        class A2(self.Base):
            id = Column(Integer, primary_key=True)
            same = Column(String)
            different2 = Column(String)
        self.create_all()
        # Prepare
        with self.db.begin():
            a1 = A1(same='s11', different1='d11')
            self.db.add(a1)
        # Replect when replection doesn't exist
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.reflect(a1, A2)
        for changes in [hist.created, hist.deleted, hist.updated]:
            self.assertFalse(changes)
        self.assertIsNone(a2)
        # Rerplicate when reflection doesn't exist
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.replicate(a1, A2)
        hist.assert_created_one(A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.id, a1.id)
        self.assertEqual(a2.same, 's11')
        self.assertIsNone(a2.different2)
        self.db.expunge(a2)
        # Reflect when reflection exists, insure attributes are not copied
        with self.db.begin():
            a1.same = 's12'
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.reflect(a1, A2)
        for changes in [hist.created, hist.deleted, hist.updated]:
            self.assertFalse(hist.updated)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.same, 's11')
        # Rerplicate when reflection exists, insure common attributes are
        # copied and own attributes are kept unchanged
        with self.db.begin():
            a2.same = 's21'
            a2.different2 = 'd21'
        self.db.expunge(a2)
        with DBHistory(self.db) as hist, self.db.begin():
            a2 = replication.replicate(a1, A2)
        hist.assert_updated_one(A2)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.same, 's12')
        self.assertEqual(a2.different2, 'd21')
