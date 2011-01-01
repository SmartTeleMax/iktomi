# -*- coding: utf-8 -*-

from . import cached_property
import math, itertools
from ..web.url import URL


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
            return paginator._page_url_pair((chunk-1)*paginator.chunk_size + 1)
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


class Paginator(object):

    limit = 0
    count = 0
    page_param = 'page'
    items = ()
    impl = staticmethod(full_page_range) # Callable returning the list of pages
                                         # to show in paginator.

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

    def invalid_page(self):
        '''This method is called when invalid page is passed in request.
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
        initialization.'''
        return URL(self.request.path)

    def page_url(self, page):
        '''Returns URL for page.'''
        if page is not None:
            return self.url.set(**{self.page_param: page})

    def _page_url_pair(self, page=None):
        return _PageURL(page, self.page_url(page))

    @cached_property
    def pages_count(self):
        '''Number of pages.'''
        if not self.limit or self.count<self.limit:
            return 1
        return int(math.ceil(float(self.count)/self.limit))

    def slice(self, items):
        '''Slice the sequence of all items to obtain them for current page.'''
        if self.limit:
            if self.page>self.pages_count:
                return []
            return items[self.limit*(self.page-1):self.limit*self.page]
        else:
            return items[:]

    def enumerate(self):
        skipped = (self.page-1)*self.limit
        return itertools.izip(itertools.count(skipped+1), self.items)

    @cached_property
    def prev(self):
        if self.page>1:
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
        return prop


class ModelPaginator(Paginator):

    def __init__(self, request, query, **kwargs):
        self._query = query
        Paginator.__init__(self, request, **kwargs)

    @cached_property
    def count(self):
        return self._query.count()

    @cached_property
    def items(self):
        return self.slice(self._query)

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)
