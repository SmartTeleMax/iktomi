# -*- coding: utf-8 -*-

from mage import CommandDigest

__all__ = ['SqlObjectCommands']

class SqlObjectCommands(CommandDigest):
    '''
    SQLObject operations:
    '''

    def __init__(self, models_module):
        from inspect import isclass
        from sqlobject import SQLObject
        from sqlobject.inheritance import InheritableSQLObject
        self.models = []
        for item_name in dir(models_module):
            item = getattr(models_module, item_name)
            if isclass(item) and (item is not SQLObject) \
            and (item is not InheritableSQLObject) \
            and issubclass(item, SQLObject):
                item._connection.debug = True
                self.models.append(item)

    def command_sync(self, db=''):
        '''
        Synchronize your models to database
        $ python manage.py sqlobject:sync [db name]
        '''
        for model in self.models:
            if db == '' or model.__module__ == db:
                model.createTable(ifNotExists=True)

    def command_drop(self, db=''):
        '''
        Drop your models in database
        $ python manage.py sqlobject:drop [db name]
        '''
        for model in self.models:
            if db == '' or model.__module__ == db:
                model.dropTable(dropJoinTables=True)

    def command_reset(self, db=''):
        '''
        Drop and Sync your models
        $ python manage.py sqlobject:reset [db name]
        '''
        for model in self.models:
            if db == '' or model.__module__ == db:
                model.dropTable(ifExists=True, dropJoinTables=True)
                model.createTable()

    def command_schema(self, model_name=''):
        '''
        Show model schema
        $ python manage.py sqlobject:schema [model name]
        '''
        #XXX: also show intermedian tables for many2many relations
        for model in self.models:
            if model_name == '' or model.__name__ == model_name:
                print ''.join(model.createTableSQL()[0])
                print ''.join(model.createTableSQL()[1])
