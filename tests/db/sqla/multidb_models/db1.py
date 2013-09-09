from sqlalchemy.schema import MetaData, Column
from sqlalchemy.types import Integer
from sqlalchemy.ext.declarative import declarative_base
from iktomi.db.sqla.declarative import AutoTableNameMeta

metadata = MetaData()
Base = declarative_base(metadata=metadata, name='Base',
                        metaclass=AutoTableNameMeta)


class SameName(Base):
    id = Column(Integer, primary_key=True)

class DifferentName1(Base):
    id = Column(Integer, primary_key=True)
