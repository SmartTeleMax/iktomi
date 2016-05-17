# i18n markers
def N_(msg):
    '''
    Single translatable string marker.
    Does nothing, just a marker for \\*.pot file compilers.

    Usage::

        n = N_('translate me')
        translated = env.gettext(n)
    '''
    return msg


class M_(object):
    '''
    Marker for translatable string with plural form.
    Does not make a translation, just incapsulates a data about
    the translatable string.

    :param single: a single form
    :param plural: a plural form. Count can be included in %\-format syntax
    :param count_field: a key used to format

    Usage::

        message = M_(u'max length is %(max)d symbol',
                     u'max length is %(max)d symbols',
                     count_field="max")
        m = message % {'max': 10}
        trans = env.ngettext(m.single,
                             m.plural,
                             m.count
                             ) % m.format_args
    '''
    def __init__(self, single, plural, count_field='count', format_args=None):
        self.single = single
        self.plural = plural
        self.count_field = count_field
        self.format_args = format_args

    def __mod__(self, format_args):
        '''
        Returns a copy of the object with bound formatting args (as dict).
        A key equal to `count_field` must be in `format_args`.
        '''
        return self.__class__(self.single, self.plural, count_field=self.count_field,
                              format_args=format_args)

    @property
    def count(self):
        '''
        A count based on `count_field` and `format_args`.
        '''
        args = self.format_args
        if args is None or \
                (isinstance(args, dict) and self.count_field not in args):
            raise TypeError("count is required")
        return args[self.count_field] if isinstance(args, dict) else args

    def __unicode__(self):
        args = self.format_args
        if self.count == 1:
            return self.single % args
        return self.plural % args






