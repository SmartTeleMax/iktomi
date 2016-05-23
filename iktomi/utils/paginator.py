# -*- coding: utf-8 -*-

from . import cached_property
import math
import six
import itertools
from six.moves import zip
if six.PY3:# pragma: no cover
    range = lambda *x: list(six.moves.range(*x)) # XXX
from ..web.reverse import URL


def full_page_range(pages_count, page):
    return range(1, pages_count+1)


class FancyPageRange(object):
    '''Insures there are edge pages are shown at each edge and surround pages
    around current page.'''

    def __init__(self, edge=3, surround=5):
        self.edge = edge
        self.surround = surround

    def __call__(self, pages_count, page):
        assert pages_count>0
        assert page>0
        ranges = []
        # left edge
        left_end = min(self.edge, pages_count)
        ranges.append([1, left_end+1])
        # around current page
        surround_start = min(max(1, page-self.surround), pages_count+1)
        surround_end = min(page+self.surround, pages_count)
        if surround_end>=surround_start:
            ranges.append([surround_start, surround_end+1])
        # right edge
        right_start = min(max(1, pages_count-self.edge+1), pages_count+1)
        if pages_count>=right_start:
            ranges.append([right_start, pages_count+1])
        # merge ranges
        ranges.sort()
        pages = range(*ranges[0])
        for current in ranges[1:]:
            last = pages[-1]
            if current[1] <= last:
                # this range is inside previous
                continue
            if current[0] <= last+2:
                # extends previous
                pages += range(last+1, current[1])
            else:
                # comes after with space
                pages += [None] + range(*current)
        return pages


class ChunkedPageRange(object):

    '''Splits pages range into chunks.'''

    def __init__(self, size=10):
        self.paginator_chunk_size = self.size = size

    def __call__(self, pages_count, page):
        assert pages_count>0
        assert page>0
        chunk = (page-1)//self.size
        start = chunk*self.size + 1
        end = min((chunk+1)*self.size, pages_count)
        return range(start, end+1)

    # Everything starting from 'paginator_' is exported to Paginator object.

    def paginator_prev_chunk(paginator):
        chunk = (paginator.page-1)//paginator.chunk_size
        if chunk:
            chunk_size = paginator.chunk_size
            return paginator._page_url_pair((chunk-1)*chunk_size + chunk_size)
        else:
            return paginator._page_url_pair()
    # Due to nature of cached_property we have to explicitly provide name.
    paginator_prev_chunk = cached_property(paginator_prev_chunk, 'prev_chunk')

    def paginator_next_chunk(paginator):
        chunk = (paginator.page-1)//paginator.chunk_size
        page = (chunk+1)*paginator.chunk_size + 1
        if page>paginator.pages_count:
            return paginator._page_url_pair()
        else:
            return paginator._page_url_pair(page)
    # Due to nature of cached_property we have to explicitly provide name.
    paginator_next_chunk = cached_property(paginator_next_chunk, 'next_chunk')


class _PageURL(tuple):

    def __new__(cls, page=None, url=None):
        return tuple.__new__(cls, (page, url))

    @property
    def page(self):
        return self[0]

    @property
    def url(self):
        return self[1]

    def __nonzero__(self):
        return self.page is not None

    __bool__ = __nonzero__


class Paginator(object):
    '''
    Paginator on top of `webob.Request`.
    '''

    #: limit of items on the page
    limit = 0
    #: total count of items
    count = 0
    #: name of GET argument
    page_param = 'page'
    #: show host in URL or not
    show_host = False
    #: items on the current page
    items = ()
    #: Callable returning the list of pages
    #: to show in paginator.
    impl = staticmethod(full_page_range)
    #: The limit of items allowed on the last page. 
    # I.e. if count=23 and orphans=3 with 10 items per page,
    # there will be 2 pages with 10 and 13 items.
    orphans = 0

    def __init__(self, request, **kwargs):
        self.request = request
        self.__dict__.update(kwargs)
        # Calculate page here in case we return 404 for invalid page
        self.page

    def __nonzero__(self):
        '''Should paginator be shown?'''
        # We have to check current page too in case the list of items just
        # shrunk to fit into one page.
        return bool(self.limit) and (self.pages_count>1 or self.page>1)

    __bool__ = __nonzero__

    def invalid_page(self):
        '''This method is called when invalid (not positive int)
        page is passed in request.
        Use "pass" to ignore. Other options are raising exceptions for HTTP
        Not Found or redirects.'''
        pass

    @cached_property
    def page(self):
        '''Current page.'''
        page = self.request.GET.get(self.page_param)
        if not page:
            return 1
        try:
            page = int(page)
        except ValueError:
            self.invalid_page()
            return 1
        if page<1:
            self.invalid_page()
            return 1
        return page

    @cached_property
    def url(self):
        '''Current or base URL. Can be redefined via keyword argument on
        initialization.

        Returns `iktomi.web.URL object.
        `'''
        return URL.from_url(self.request.url, show_host=self.show_host)

    def page_url(self, page):
        '''
        Returns URL for page, page is included as query parameter.

        Can be redefined by keyword argument
        '''
        if page is not None and page != 1:
            return self.url.qs_set(**{self.page_param: page})
        elif page is not None:
            return self.url.qs_delete('page')

    def _page_url_pair(self, page=None):
        return _PageURL(page, self.page_url(page) if page is not None else None)

    @cached_property
    def pages_count(self):
        '''Number of pages.'''
        if not self.limit or self.count<self.limit:
            return 1
        if self.count % self.limit <= self.orphans:
            return self.count // self.limit
        return int(math.ceil(float(self.count)/self.limit))

    def slice(self, items):
        '''Slice the sequence of all items to obtain them for current page.'''
        if self.limit:
            if self.page>self.pages_count:
                return []
            if self.page == self.pages_count:
                return items[self.limit*(self.page-1):]
            return items[self.limit*(self.page-1):self.limit*self.page]
        else:
            return items[:]

    def enumerate(self):
        skipped = (self.page-1)*self.limit
        return zip(itertools.count(skipped+1), self.items)

    @cached_property
    def prev(self):
        if self.page>self.pages_count:
            # if we are on non-existing page which is higher
            # than current page, return last page, so we can navigate
            # to it
            return self.last
        elif self.page>1:
            return self._page_url_pair(self.page-1)
        else:
            return self._page_url_pair()

    @cached_property
    def next(self):
        if self.page<self.pages_count:
            return self._page_url_pair(self.page+1)
        else:
            return self._page_url_pair()

    @cached_property
    def first(self):
        return self._page_url_pair(1)

    @cached_property
    def last(self):
        return self._page_url_pair(self.pages_count)

    @cached_property
    def pages(self):
        pages = self.impl(self.pages_count, self.page)
        return [self._page_url_pair(page) for page in pages]

    def __getattr__(self, requested_name):
        name = 'paginator_'+requested_name
        impl_type = type(self.impl)
        # Look for exported descriptors defined in impl first.
        # We can't lookup in __dict__ since this doesn't work for inheritted
        # attributes.
        if name not in dir(impl_type):
            return getattr(self.impl, name)
        prop = getattr(impl_type, name)
        # The following will work only if descriptor returns self when
        # accessed in class.
        if hasattr(prop, '__get__'):
            return prop.__get__(self, type(self))
        return prop # pragma: no cover


class ModelPaginator(Paginator):

    '''
    Paginator for sqlalchemy query.
    '''

    def __init__(self, request, query, **kwargs):
        self._query = query
        Paginator.__init__(self, request, **kwargs)

    @cached_property
    def count(self):
        return self._query.count()

    @cached_property
    def items(self):
        '''Items on the current page. Filled in automatically based on query
        and currrent page'''
        return self.slice(self._query)

    def __getitem__(self, key):
        return self.items[key]

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)
