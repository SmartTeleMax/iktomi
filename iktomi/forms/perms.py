# -*- coding: utf-8 -*-
'''
This module contains basic form access control classes.

You can set permissions to form and fields like this::

    class SampleForm(form.Form):
       permissions = 'rwcx'
       fields=[fields.Field('input',
                            permissions='rw')]

or define your own permission logic::

    class SampleForm(form.Form):
       permissions = 'rwcx'
       fields=[fields.Field('input',
                            perm_getter=UserBasedPerm({'admin': 'rw',
                                                       'user': 'r'}))]


or pass form permissions to constructor::

    >>> form = SampleForm(env, data, permissions='rw')

To access current permissions set you can use field's :attr:`permissions`
property:

    >>> form.get_field('input').permissions
    set(['r', 'w'])

'''

DEFAULT_PERMISSIONS = set('rwc')


class FieldPerm(object):
    '''
    Default permission getter for Field objects

    Ancestor should override the :meth:`check` method. They can use field.env
    to get any values from outside. For example::

        class RoleBased(FieldPerm):
            def __init__(self, role_perms):
                self.role_perms = role_perms

            def check(self, field):
                user = field.env.user
                perms = set(self.role_perms.get('*', ''))
                for role in user.roles:
                    perms.update(self.role_perms.get(role, ''))
                return perms
    '''

    permissions = None

    def __init__(self, permissions=None):
        if permissions is not None:
            self.permissions = set(permissions)

    def get_perms(self, obj):
        '''
        Returns combined Environment's and object's permissions.
        Resulting condition is intersection of them.
        '''
        return self.available(obj) & self.check(obj)

    def available(self, field):
        '''
        Returns permissions according environment's limiting condition.
        Determined by object's context

        Allows only field's parents' permissions
        '''
        return field.parent.permissions

    def check(self, field):
        '''
        Returns permissions determined by object itself
        '''
        if self.permissions is None:
            return field.parent.permissions
        return self.permissions

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(self.permissions))

