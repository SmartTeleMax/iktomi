import warnings
from sqlalchemy.orm.collections import InstrumentedList

warnings.warn('OrderedList is deprecated. Use '\
                'sqlalchemy.ext.orderinglist.ordering_list() instead',
              category=DeprecationWarning)


class OrderedList(InstrumentedList):
    '''This collection automatically updates order column to preserve original
    order of items when they are loaded with corresponding ORDER BY clause.'''

    order_column = 'order'

    def append(self, item):
        if self:
            order = getattr(self[-1], self.order_column)+1
        else:
            order = 1
        setattr(item, self.order_column, order)
        InstrumentedList.append(self, item)
