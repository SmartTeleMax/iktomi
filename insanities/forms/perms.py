# -*- coding: utf-8 -*-
'''
This module contains basic form access control classes.

You can set permissions to form and fields like this::

    class SampleForm(form.Form):
       permissions = 'rwcx'
       fields=[fields.Field('input',
                            perm_getter=perms.SimplePerm('rw'))]

or pass form permissions to constructor::

    >>> form = SampleForm(env, data, permissions='rw')

To access current permissions set you can use field's :attr:`permissions`
property:
    
    >>> form.get_field('input').permissions
    set(['r', 'w'])

'''

DEFAULT_PERMISSIONS = set('rwc')

class BasePerm(object):
    """
    Permission getters base class.

    Describes the interface for classes, designed for determine permissions of
    different objects, particularly Form Fields.
    """
    
    def get_perms(self, obj):
        '''
        Returns combined Environment's and object's permissions.
        Resulting condition is intersection of them.
        '''
        return self.available(obj) & self.check(obj)

    def available(self, obj):
        '''
        Returns permissions according environment's limiting condition.
        Determined by object's context
        
        Ancestors must override this method
        '''
        return DEFAULT_PERMISSIONS
    
    def check(self, obj):
        '''
        Returns permissions determined by object itself

        Ancestors must override this method
        '''
        return DEFAULT_PERMISSIONS


class FieldPerm(BasePerm):
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
    
    def available(self, field):
        '''
        Allows only field's parents' permissions
        '''
        return field.parent.permissions

    def check(self, field):
        '''
        Returns permissions determined by object itself

        Ancestors must override this method
        '''
        return field.parent.permissions
    
    
class SimplePerm(FieldPerm):
    '''
    Permission getter returning determined set of permissions
    '''

    def __init__(self, permissions):
        self.permissions = set(permissions)
        
    def check(self, field):
        return self.permissions


'''
'''