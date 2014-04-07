import unittest
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from iktomi.unstable.db.sqla.public_query import PublicQuery


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    public = Column(Boolean, nullable=False)
    addresses = relation("Address", backref="user")
    photos = relation("Photo", secondary="user_photo")


class UserWithJoinedAddresses(User):

    __tablename__ = None

    addresses = relation("Address", lazy="joined")
    photos = relation("Photo", secondary="user_photo", lazy="joined")


class Address(Base):
    __tablename__ = 'address'

    id = Column(Integer, primary_key=True)
    email = Column(String(100))
    user_id = Column(Integer, ForeignKey('user.id'))
    public = Column(Boolean, nullable=False)


class User_Photo(Base):
    __tablename__ = 'user_photo'

    user_id = Column(ForeignKey('user.id'), nullable=False, primary_key=True)
    photo_id = Column(ForeignKey('photo.id'), nullable=False, primary_key=True)


class Photo(Base):
    __tablename__ = 'photo'

    id = Column(Integer, primary_key=True)
    photo = Column(String(100))
    public = Column(Boolean, nullable=False)


class WithAttributeError(Base):
    __tablename__ = 'with_attribute_error'

    id = Column(Integer, primary_key=True)
    @hybrid_property
    def public(self):
        # Mimic nested error
        raise AttributeError('some_attribute')

class Doc(Base):
    __tablename__ = 'doc'

    NEWS = 1
    ANNOUNCE = 2

    id = Column(Integer, primary_key=True)
    type = Column(Integer)
    title = Column(String(100))
    public = Column(Boolean)

    __mapper_args__ = {'polymorphic_on': type}

    def __new__(cls, **initial):
        if 'type' in initial:
            cls = {Doc.NEWS: News,
                   Doc.ANNOUNCE: Announce}[initial['type']]
        return Base.__new__(cls)


class News(Doc):

    __mapper_args__ = {'polymorphic_identity': Doc.NEWS}


class Announce(Doc):
    __tablename__ = 'announce'

    id = Column(Integer, ForeignKey(Doc.id), nullable=False, primary_key=True)
    date_start = Column(String(100))

    __mapper_args__ = {'polymorphic_identity': Doc.ANNOUNCE}


class NotFiltered(Base):
    __tablename__ = 'not_filtered'

    id = Column(Integer, nullable=False, primary_key=True)


class UserAddressesTest(unittest.TestCase):
    '''
    Simple set of tests with the same set of initial objects from original
    recipe at http://www.sqlalchemy.org/trac/wiki/UsageRecipes/PreFilteredQuery
    '''

    QUERY_CLS = PublicQuery

    def setUp(self):
        engine = create_engine('sqlite://')#, echo=True)
        Base.metadata.create_all(engine)
        # Some solutions doen't allow creating objects with PublicQuery, so we
        # setup separate session for it.
        # dba = (all) session with standard Query class
        # dbp = (public) session with tested PublicQuery class
        self.dba = sessionmaker(bind=engine)()
        self.dba.add_all([
            User(name='u1', public=True,
                 addresses=[Address(email='u1a1', public=True),
                            Address(email='u1a2', public=True)],
                 photos=[Photo(photo='u1p1', public=True),
                         Photo(photo='u1p2', public=True)]),
            User(name='u2', public=True,
                 addresses=[Address(email='u2a1', public=False),
                            Address(email='u2a2', public=True)],
                 photos=[Photo(photo='u2p1', public=False),
                         Photo(photo='u2p2', public=True)]),
            User(name='u3', public=False,
                 addresses=[Address(email='u3a1', public=False),
                            Address(email='u3a2', public=False)],
                 photos=[Photo(photo='u3p1', public=False),
                         Photo(photo='u3p2', public=False)]),
            User(name='u4', public=False,
                 addresses=[Address(email='u4a1', public=False),
                            Address(email='u4a2', public=True)],
                 photos=[Photo(photo='u3p1', public=False),
                         Photo(photo='u3p2', public=False)]),
            User(name='u5', public=True,
                 addresses=[Address(email='u5a1', public=True),
                            Address(email='u5a2', public=False)],
                 photos=[Photo(photo='u5p1', public=True),
                         Photo(photo='u5p2', public=False)]),
            User(name='u6', public=True,
                 addresses=[Address(email='u6a1', public=False),
                            Address(email='u6a2', public=False)],
                 photos=[Photo(photo='u6p1', public=False),
                         Photo(photo='u6p2', public=False)]),
            WithAttributeError(),
            News(title='n1', public=True),
            Announce(title='a1', public=True, date_start='tomorrow'),
            NotFiltered(id=1),
            NotFiltered(id=2),
            NotFiltered(id=3),
            NotFiltered(id=4),
        ])
        self.dba.commit()
        self.dbp = sessionmaker(bind=engine, query_cls=self.QUERY_CLS)()

    def tearDown(self):
        self.dba.close()
        self.dbp.close()

    def test_public(self):
        # This test doesn't depend on initial state of DB
        for user in self.dbp.query(User):
            self.assertTrue(user.public)
        for addr in self.dbp.query(Address):
            self.assertTrue(addr.public)

    def test_query_iter(self):
        names = [u.name for u in self.dbp.query(User)]
        self.assertEqual(names, ['u1', 'u2', 'u5', 'u6'])
        emails = [a.email for a in self.dbp.query(Address)]
        self.assertEqual(emails, ['u1a1', 'u1a2', 'u2a2', 'u4a2', 'u5a1'])

    def test_query_field(self):
        names = set(n for (n,) in self.dbp.query(User.name))
        self.assertEqual(names, set(['u1', 'u2', 'u5', 'u6']))
        emails = set(e for (e,) in self.dbp.query(Address.email))
        self.assertEqual(emails, set(['u1a1', 'u1a2', 'u2a2', 'u4a2', 'u5a1']))

    def test_relation_list(self):
        for name, emails in {'u1': ['u1a1', 'u1a2'],
                             'u2': ['u2a2'],
                             'u5': ['u5a1'],
                             'u6': []}.items():
            user = self.dbp.query(User).filter_by(name=name).scalar()
            self.assertEqual(set(a.email for a in user.addresses), set(emails))

    def test_mtm_relation_list(self):
        for name, photos in {'u1': ['u1p1', 'u1p2'],
                             'u2': ['u2p2'],
                             'u5': ['u5p1'],
                             'u6': []}.items():
            user = self.dbp.query(User).filter_by(name=name).scalar()
            self.assertEqual(set(a.photo for a in user.photos), set(photos))

    def test_relation_scalar(self):
        for email, name in {'u1a1': 'u1',
                            'u1a2': 'u1',
                            'u2a2': 'u2',
                            'u4a2': None,
                            'u5a1': 'u5'}.items():
            addr = self.dbp.query(Address).filter_by(email=email).scalar()
            if name is None:
                self.assertIsNone(addr.user)
            else:
                self.assertEqual(addr.user.name, name)

    def test_count(self):
        self.assertEqual(self.dbp.query(User).count(), 4)
        self.assertEqual(self.dbp.query(Address).count(), 5)

    def test_func_count(self):
        self.assertEqual(self.dbp.query(func.count(User.id)).scalar(), 4)
        self.assertEqual(self.dbp.query(func.count(Address.id)).scalar(), 5)

    def test_get(self):
        for user_id, in self.dba.query(User.id)\
                    .filter(User.name.in_(['u1', 'u2', 'u5', 'u6'])):
            user = self.dbp.query(User).get(user_id)
            self.assertIsNotNone(user)
        for user_id, in self.dba.query(User.id)\
                    .filter(User.name.in_(['u3', 'u4'])):
            user = self.dbp.query(User).get(user_id)
            self.assertIsNone(user)

    def test_relation_after_change(self):
        user = self.dbp.query(User).filter_by(name='u1').scalar()
        self.assertEqual(len(user.addresses), 2)
        addr1, addr2 = user.addresses
        self.assertIsNotNone(addr1.user)
        self.assertIsNotNone(addr2.user)
        addr2.public = False
        self.dbp.commit()
        self.assertEqual(len(user.addresses), 1)
        self.assertIsNotNone(addr1.user)
        user.public = False
        self.dbp.commit()
        self.assertIsNone(addr1.user)

    def test_private_by_public_join(self):
        query = self.dbp.query(User).join(User.addresses)\
                    .filter(Address.email=='u4a2')
        self.assertEqual(query.count(), 0)
        self.assertEqual(query.all(), [])

    def test_private_by_public_exists(self):
        query = self.dbp.query(User).filter(User.addresses.any(email='u4a2'))
        self.assertEqual(query.count(), 0)
        self.assertEqual(query.all(), [])

    def test_public_by_private_join(self):
        query = self.dbp.query(User).join(User.addresses)\
                    .filter(Address.email=='u2a1')
        self.assertEqual(query.count(), 0)
        self.assertEqual(query.all(), [])

    def test_mtm_public_by_private_join(self):
        query = self.dbp.query(User).join(User.photos)\
                    .filter(Photo.photo=='u2p1')
        self.assertEqual(query.count(), 0)
        self.assertEqual(query.all(), [])

    @unittest.skip('test from sa_public_query')
    def test_public_by_private_exists(self):
        query = self.dbp.query(User).filter(User.addresses.any(email='u2a1'))
        self.assertEqual(query.count(), 0)
        self.assertEqual(query.all(), [])

    def test_join_pairs(self):
        query = self.dbp.query(User.name, Address.email).join(Address.user)
        self.assertEqual(set(query.all()),
                         set([('u1', 'u1a1'),
                              ('u1', 'u1a2'),
                              ('u2', 'u2a2'),
                              ('u5', 'u5a1')]))

    @unittest.skip('test from sa_public_query')
    def test_relation_group_count(self):
        query = self.dbp.query(User.name, func.count(Address.id))\
                        .outerjoin(User.addresses).group_by(User.id)
        count_by_name = dict(query.all())
        self.assertEqual(count_by_name, {'u1': 2, 'u2': 1, 'u5': 1, 'u6': 0})

    def test_joinedload(self):
        for name, emails, photos in [
                ('u1', ['u1a1', 'u1a2'], ['u1p1', 'u1p2']),
                ('u2', ['u2a2'], ['u2p2']),
                ('u3', None, None),
                ('u4', None, None),
                ('u5', ['u5a1'], ['u5p1']),
                ('u6', [], [])]:
            query = self.dbp.query(User).filter_by(name=name).\
                             options(joinedload(User.addresses)).\
                             options(joinedload(User.photos))
            user = query.scalar()
            if emails is None:
                self.assertIsNone(user)
            else:
                self.assertEqual(set(a.email for a in user.addresses),
                                 set(emails))
            if photos is not None:
                self.assertEqual(set(p.photo for p in user.photos),
                                 set(photos))


    def test_lazy_joined(self):
        for name, emails, photos in [
                ('u1', ['u1a1', 'u1a2'], ['u1p1', 'u1p2']),
                ('u2', ['u2a2'], ['u2p2']),
                ('u3', None, None),
                ('u4', None, None),
                ('u5', ['u5a1'], ['u5p1']),
                ('u6', [], [])]:
            query = self.dbp.query(UserWithJoinedAddresses).filter_by(name=name)
            user = query.scalar()
            if emails is None:
                self.assertIsNone(user)
            else:
                self.assertEqual(set(a.email for a in user.addresses),
                                 set(emails))
            if photos is not None:
                self.assertEqual(set(p.photo for p in user.photos),
                                 set(photos))

    def test_attribute_error(self):
        # Test for possible security issue due to misinterpreted AttibuteError
        with self.assertRaises(AttributeError):
            self.dbp.query(WithAttributeError).all()

    def test_limit(self):
        users = self.dbp.query(User).limit(3)
        self.assertEqual(set([x.name for x in users]),
                         set(['u1', 'u2', 'u5']))

    def test_offset(self):
        users = self.dbp.query(User).offset(1)
        self.assertEqual(set([x.name for x in users]),
                         set(['u2', 'u5', 'u6']))

    def test_slice(self):
        users = self.dbp.query(User)[:3]
        self.assertEqual(set([x.name for x in users]),
                         set(['u1', 'u2', 'u5']))
        users = self.dbp.query(User)[:]
        self.assertEqual(set([x.name for x in users]),
                         set(['u1', 'u2', 'u5', 'u6']))
        users = self.dbp.query(User)[:-1]
        self.assertEqual(set([x.name for x in users]),
                         set(['u1', 'u2', 'u5']))
        users = self.dbp.query(User)[1:]
        self.assertEqual(set([x.name for x in users]),
                         set(['u2', 'u5', 'u6']))
        users = self.dbp.query(User)[1:3]
        self.assertEqual(set([x.name for x in users]),
                         set(['u2', 'u5']))
        users = self.dbp.query(User)[::2]
        self.assertEqual(set([x.name for x in users]),
                         set(['u1', 'u5']))

    def test_limit_not_filtered(self):
        obj = self.dbp.query(NotFiltered).limit(1)[0]
        self.assertEqual(obj.id, 1)

        obj = self.dbp.query(NotFiltered).offset(1)[0]
        self.assertEqual(obj.id, 2)

        obj = self.dbp.query(NotFiltered)[1:2][0]
        self.assertEqual(obj.id, 2)

    def test_subclass_lazy(self):
        doc = self.dbp.query(Doc).filter_by(title='a1').scalar()
        self.assertEqual(doc.date_start, 'tomorrow')

