# -*- coding: utf-8 -*-

import unittest
from iktomi.cli.sqla import Sqla
from sqlalchemy import create_engine, Column, Integer, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import MEDIUMTEXT

__all__ = ['SchemaTests']


class SchemaTests(unittest.TestCase):

    def test_specific_dialect(self):
        Base = declarative_base()
        class Obj(Base):
            __tablename__ = 'Obj'
            id = Column(Integer, primary_key=True)
            text = Column(MEDIUMTEXT)
        engine = create_engine('mysql+pymysql://')
        cli = Sqla(orm.sessionmaker(bind=engine))
        schema = cli._schema(Obj.__table__)
        self.assertIn('MEDIUMTEXT', schema)
