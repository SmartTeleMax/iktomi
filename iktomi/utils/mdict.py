# -*- coding: utf-8 -*-

class MultiDict(dict):
    """
    Dictionary that allows to map multiple ``values``
    to one ``key``.

    >>> md = MultiDict((('foo', 'bar'), ('spam', 'eggs'), ('foo', 'baz')))
    >>> md['foo']
    ['bar', 'baz']
    >>> md['spam']
    ['eggs']
    >>> md.getlist('foo')
    ['bar', 'baz']
    """

    def __init__(self, initial_data={}, *args, **kwargs):
        """
        .. describe:: initial_data

           Iterable with items represented as tuple or list of ``key``, ``value``.
           Or ``dict`` object, or other ``MultiDict`` object.

        >>> list_ = (('foo','bar'),('spam','eggs'),('foo','baz'))
        >>> md = MultiDict(list_)
        >>> print md
        MultiDict([('foo', 'bar'), ('foo', 'baz'), ('spam', 'eggs')])
        >>> new_md = MultiDict(md)
        >>> print new_md
        MultiDict([('foo', 'bar'), ('foo', 'baz'), ('spam', 'eggs')])
        """
        super(MultiDict, self).__init__(*args, **kwargs)

        if hasattr(initial_data, 'items'):
            # Предполагаем, что initial_data - словарь или экземпляр
            # MultiDict. Просто сохранить копию словаря нельзя, потому что
            # внутреннее представление данных - словарь, каждому
            # ключу которого соответствует список значений
            initial_data = initial_data.items()

        for key, value in initial_data:
            self.append(key, value)

    def append(self, key, value):
        """
        Method appends ``value`` for ``key``, if ``key`` doesn't
        exists it will be created.

        >>> md = MultiDict()
        >>> md.append('foo', 'bar')
        >>> md.append('foo', 'baz')
        >>> md.append('spam', 'eggs')
        >>> print md
        MultiDict([('foo', 'bar'), ('foo', 'baz'), ('spam', 'eggs')])
        """
        self.setdefault(key, []).append(value)

    getlist = dict.__getitem__

    def getfirst(self, key):
        """
        Method returns first value from values list
        of the ``key``.

        >>> md = MultiDict((('foo', 'bar'), ('spam', 'eggs'), ('foo', 'baz')))
        >>> md.getfirst('spam')
        'eggs'
        >>> md.getfirst('foo')
        'bar'
        """
        return super(MultiDict, self).__getitem__(key)[0]

    def getlast(self, key):
        """
        Method returns last value from values list
        of the ``key``.

        >>> md = MultiDict((('foo', 'bar'), ('spam', 'eggs'), ('foo', 'baz')))
        >>> md.getlast('spam')
        'eggs'
        >>> md.getlast('foo')
        'baz'
        """
        return super(MultiDict, self).__getitem__(key)[-1]

    def __setitem__(self, key, value):
        """
        Method maps ``value`` to ``key``

        .. describe:: value
           
           ``list`` or ``tuple``

        >>> md = MultiDict()
        >>> md['foo'] =  'bar'# doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        AssertionError: Values must be type list or tuple
        >>> md['foo'] = ['spam', 'eggs']
        >>> print md
        MultiDict([('foo', 'spam'), ('foo', 'eggs')])
        """
        assert isinstance(value, list),\
                "Values must be type list"
        super(MultiDict, self).__setitem__(key, value)

    # Метод вернется, если надумаем делать setone()
    #setlist = __setitem__

    def update(self, items):
        raise NotImplementedError


    def items(self):
        """
        Method returns list of tuples (``key``, ``value``).
        If ``key`` has multiple values, then multiple tuples
        will be returned for this ``key``.

        >>> md = MultiDict((('foo', 'bar'), ('spam', 'eggs'), ('foo', 'baz')))
        >>> md.items()
        [('foo', 'bar'), ('foo', 'baz'), ('spam', 'eggs')]
        """
        return list(self.iteritems())

    def iteritems(self):
        for k,v in super(MultiDict, self).iteritems():
            for item in v:
                yield (k, item)

    def copy(self):
        return self.__class__(self)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.items())
