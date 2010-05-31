# -*- coding: utf-8 -*-

import models


def add_admin(db):
    admin = models.User(name='Admin', login='admin')
    admin.set_password('admin')
    db.add(admin)


def initial(db):
    add_admin(db)
    db.commit()
