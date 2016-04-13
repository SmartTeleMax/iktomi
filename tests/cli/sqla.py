# -*- coding: utf-8 -*-

import re
import sys
import unittest
from cStringIO import StringIO
from iktomi.cli.sqla import Sqla, drop_everything
from sqlalchemy import (
    create_engine, orm, MetaData, Column, Integer, ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import MEDIUMTEXT
try:
    from unittest import mock
except ImportError:
    import mock

__all__ = ['SqlaTests']


class SqlaTests(unittest.TestCase):

    def test_drop_everything(self):
        # Prepare.
        # Non-trivial case with circular foreign key constraints.
        # SQLite doesn't support dropping constraint by name and creation of
        # custom types, so these cases are not covered by the test.
        Base = declarative_base()

        class A(Base):
            __tablename__ = 'A'
            id = Column(Integer, primary_key=True)
            b_id = Column(ForeignKey('B.id', use_alter=True))

        class B(Base):
            __tablename__ = 'B'
            id = Column(Integer, primary_key=True)
            a_id = Column(ForeignKey(A.id))

        engine = create_engine('sqlite://')
        Base.metadata.create_all(bind=engine)
        self.assertTrue(engine.has_table('A'))
        self.assertTrue(engine.has_table('B'))

        # Actual test
        drop_everything(engine)
        self.assertFalse(engine.has_table('A'))
        self.assertFalse(engine.has_table('B'))

    def test_specific_dialect(self):
        Base = declarative_base()

        class Obj(Base):
            __tablename__ = 'Obj'
            id = Column(Integer, primary_key=True)
            text = Column(MEDIUMTEXT)

        engine = create_engine('mysql+pymysql://')
        cli = Sqla(orm.sessionmaker(bind=engine), metadata=Base.metadata)
        schema = cli._schema(Obj.__table__)
        self.assertIn('MEDIUMTEXT', schema)

    def test_create_drop_tables_single_meta(self):
        Base = declarative_base()

        class A(Base):
            __tablename__ = 'A'
            id = Column(Integer, primary_key=True)

        engine = create_engine('sqlite://')
        cli = Sqla(orm.sessionmaker(bind=engine), metadata=Base.metadata)

        for verbose in [False, True]:

            cli.command_create_tables(verbose=verbose)
            self.assertTrue(engine.has_table('A'))
            with mock.patch.object(sys.stdin, 'readline', return_value='n'):
                try:
                    cli.command_drop_tables()
                except SystemExit:
                    pass
            self.assertTrue(engine.has_table('A'))

            with mock.patch.object(sys.stdin, 'readline', return_value='y'):
                cli.command_drop_tables()
            self.assertFalse(engine.has_table('A'))

    def test_create_drop_tables_several_meta(self):
        Base1 = declarative_base()

        class A1(Base1):
            __tablename__ = 'A'
            id = Column(Integer, primary_key=True)

        Base2 = declarative_base()

        class A2(Base2):
            __tablename__ = 'A'
            id = Column(Integer, primary_key=True)

        engine1 = create_engine('sqlite://')
        engine2 = create_engine('sqlite://')
        binds = {
            A1.__table__: engine1,
            A2.__table__: engine2,
        }
        meta = {
            'm1': Base1.metadata,
            'm2': Base2.metadata,
            'm3': MetaData(),
        }
        cli = Sqla(orm.sessionmaker(binds=binds), metadata=meta)

        for verbose in [False, True]:

            cli.command_create_tables(verbose=verbose)
            self.assertTrue(engine1.has_table('A'))
            self.assertTrue(engine2.has_table('A'))

            with mock.patch.object(sys.stdin, 'readline', return_value='y'):
                cli.command_drop_tables('m1')
            self.assertFalse(engine1.has_table('A'))
            self.assertTrue(engine2.has_table('A'))

            with mock.patch.object(sys.stdin, 'readline', return_value='y'):
                cli.command_drop_tables()
            self.assertFalse(engine1.has_table('A'))
            self.assertFalse(engine2.has_table('A'))

            cli.command_create_tables('m1', verbose=verbose)
            self.assertTrue(engine1.has_table('A'))
            self.assertFalse(engine2.has_table('A'))

            with mock.patch.object(sys.stdin, 'readline', return_value='y'):
                cli.command_drop_tables()
            self.assertFalse(engine1.has_table('A'))
            self.assertFalse(engine2.has_table('A'))

            cli.command_create_tables('m3', verbose=verbose)
            self.assertFalse(engine1.has_table('A'))
            self.assertFalse(engine2.has_table('A'))

    def test_reset(self):
        Base = declarative_base()

        class A(Base):
            __tablename__ = 'A'
            id = Column(Integer, primary_key=True)

        id_values = [id_value1, id_value2] = [12, 34]

        # Each time it uses different value
        def initial(db):
            db.add(A(id=id_values.pop(0)))

        engine = create_engine('sqlite://')
        cli = Sqla(orm.sessionmaker(bind=engine), metadata=Base.metadata,
                   initial=initial)

        with mock.patch.object(sys.stdin, 'readline', return_value='y'):
            cli.command_reset()
        query = cli.session.query(A)
        self.assertEqual(query.count(), 1)
        a = query.one()
        self.assertEqual(a.id, id_value1)

        with mock.patch.object(sys.stdin, 'readline', return_value='y'):
            cli.command_reset()
        query = cli.session.query(A)
        self.assertEqual(query.count(), 1)
        a = query.one()
        self.assertEqual(a.id, id_value2)

    _created_tables = re.compile(r'create\s+table\s+\W?(\w+)', re.I).findall

    def test_schema_single_meta(self):
        Base = declarative_base()

        class A(Base):
            __tablename__ = 'A'
            id = Column(Integer, primary_key=True)

        class B(Base):
            __tablename__ = 'B'
            id = Column(Integer, primary_key=True)

        engine = create_engine('sqlite://')
        cli = Sqla(orm.sessionmaker(bind=engine), metadata=Base.metadata)

        output = StringIO()
        with mock.patch.object(sys, 'stdout', output):
            cli.command_schema()
        created = self._created_tables(output.getvalue())
        self.assertEqual(len(created), 2)
        self.assertEqual(created.count('A'), 1)
        self.assertEqual(created.count('B'), 1)

        output = StringIO()
        with mock.patch.object(sys, 'stdout', output):
            cli.command_schema('A')
        created = self._created_tables(output.getvalue())
        self.assertEqual(created, ['A'])

        output = StringIO()
        with mock.patch.object(sys, 'stdout', output):
            try:
                cli.command_schema('C')
            except SystemExit:
                pass
        created = self._created_tables(output.getvalue())
        self.assertEqual(created, [])

    def test_schema_several_meta(self):
        Base1 = declarative_base()

        class A1(Base1):
            __tablename__ = 'A'
            id = Column(Integer, primary_key=True)

        class B1(Base1):
            __tablename__ = 'B'
            id = Column(Integer, primary_key=True)

        Base2 = declarative_base()

        class A2(Base2):
            __tablename__ = 'A'
            id = Column(Integer, primary_key=True)

        engine1 = create_engine('sqlite://')
        engine2 = create_engine('sqlite://')
        binds = {
            A1.__table__: engine1,
            B1.__table__: engine1,
            A2.__table__: engine2,
        }
        meta = {
            'm1': Base1.metadata,
            'm2': Base2.metadata,
            'm3': MetaData(),
        }
        cli = Sqla(orm.sessionmaker(binds=binds), metadata=meta)

        output = StringIO()
        with mock.patch.object(sys, 'stdout', output):
            cli.command_schema()
        created = self._created_tables(output.getvalue())
        self.assertEqual(len(created), 3)
        self.assertEqual(created.count('A'), 2)
        self.assertEqual(created.count('B'), 1)

        output = StringIO()
        with mock.patch.object(sys, 'stdout', output):
            cli.command_schema('m1')
        created = self._created_tables(output.getvalue())
        self.assertEqual(len(created), 2)
        self.assertEqual(created.count('A'), 1)
        self.assertEqual(created.count('B'), 1)

        output = StringIO()
        with mock.patch.object(sys, 'stdout', output):
            cli.command_schema('m1.B')
        created = self._created_tables(output.getvalue())
        self.assertEqual(created, ['B'])

        output = StringIO()
        with mock.patch.object(sys, 'stdout', output):
            try:
                cli.command_schema('m2.B')
            except SystemExit:
                pass
        created = self._created_tables(output.getvalue())
        self.assertEqual(created, [])

        output = StringIO()
        with mock.patch.object(sys, 'stdout', output):
            try:
                cli.command_schema('m3.A')
            except SystemExit:
                pass
        created = self._created_tables(output.getvalue())
        self.assertEqual(created, [])

    def test_gen(self):
        gen_a = mock.MagicMock()
        cli = Sqla(orm.sessionmaker(), MetaData(), generators={'a': gen_a})
        try:
            cli.command_gen()
        except SystemExit:
            pass
        gen_a.assert_not_called()

        gen_a.reset_mock()
        cli.command_gen('a')
        gen_a.assert_called_once_with(cli.session, 0)

        gen_a.reset_mock()
        cli.command_gen('a:123')
        gen_a.assert_called_once_with(cli.session, 123)
