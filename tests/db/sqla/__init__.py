import unittest
from sqlalchemy.exc import UnboundExecutionError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from iktomi.db.sqla import multidb_binds
from . import multidb_models
from .multidb_models import db1, db2


class MultidbTest(unittest.TestCase):

    def setUp(self):
        binds = multidb_binds({'db1': 'sqlite://', 'db2': 'sqlite://'},
                              package=multidb_models)
        self.db = sessionmaker(binds=binds)()
        db1.metadata.create_all(bind=self.db.get_bind(db1.SameName))
        db1.metadata.create_all(bind=self.db.get_bind(db2.SameName))

    def test_get_bind(self):
        with self.assertRaises(UnboundExecutionError):
            # Insure it's not bound to single engine
            self.db.get_bind()
        engine_common1 = self.db.get_bind(db1.SameName)
        engine_common2 = self.db.get_bind(db2.SameName)
        self.assertIsNot(engine_common1, engine_common2)
        engine_different1 = self.db.get_bind(db1.DifferentName1)
        self.assertIs(engine_common1, engine_different1)
        engine_different2 = self.db.get_bind(db2.DifferentName2)
        self.assertIs(engine_common2, engine_different2)

    def test_query_class(self):
        try:
            self.db.query(db1.SameName).all()
        except UnboundExecutionError as exc:
            self.fail('Unexpected exception: {}'.format(exc))

    def test_query_attr(self):
        try:
            self.db.query(db1.SameName.id).all()
        except UnboundExecutionError as exc:
            self.fail('Unexpected exception: {}'.format(exc))

    def test_query_func(self):
        try:
            self.db.query(func.max(db1.SameName.id)).all()
        except UnboundExecutionError as exc:
            self.fail('Unexpected exception: {}'.format(exc))
