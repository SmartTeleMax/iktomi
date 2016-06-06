from PIL import Image


class Resizer(object):

    def __init__(self, expand=False, filter=Image.ANTIALIAS):
        self.expand = expand
        self.filter = filter

    def do__crop(self, img, transformation, params):
        return img.crop(params)

    def do__resize(self, img, transformation, params):
        return img.resize(params, self.filter)

    def new_size__resize(self, size, target_size, params):
        return params

    def new_size__crop(self, size, target_size, params):
        return (params[2] - params[0], params[3] - params[1])

    def transformations(self, size, target_size): # pragma: no cover
        '''
        Method describing transformations applied to the image,
        must be redefined in subclasses.

        Should return a list of JSON-serializable commands
        that are processed with transform method.
        Transformations can be dumped and applied on different place,
        for example, in Javascript
        '''
        raise NotImplementedError

    def transform(self, img, transformation, params):
        '''
        Apply transformations to the image.

        New transformations can be defined as methods::

            def do__transformationname(self, img, transformation, params):
                'returns new image with transformation applied'
                ...

            def new_size__transformationname(self, size, target_size, params):
                'dry run, returns a size of image if transformation is applied'
                ...
        '''
        # Transformations MUST be idempotent.
        # The limitation is caused by implementation of
        # image upload in iktomi.cms.
        # The transformation can be applied twice:
        # on image upload after crop (when TransientFile is created)
        # and on object save (when PersistentFile is created).
        method = getattr(self, 'do__' + transformation)
        return method(img, transformation, params)

    def get_target_size(self, size, target_size):
        transforms = self.transformations(size, target_size)
        for transformation, params in transforms:
            method = getattr(self, 'new_size__' + transformation)
            size = method(size, target_size, params)
        return size

    def __call__(self, img, target_size):
        transforms = self.transformations(img.size, target_size)
        for transformation, params in transforms:
            img = self.transform(img, transformation, params)
        return img


class ResizeFit(Resizer):

    '''
    Resizes an image in a way it fits to a given rectangle.

    :param expand: force expand image to the rectangle.
    '''

    def transformations(self, size, target_size):
        sw, sh = size
        tw, th = target_size
        if not self.expand and sw<=tw and sh<=th:
            return []

        if sw*th>sh*tw:
            h = sh*tw//sw
            return [('resize', (tw, h))]
        else:
            w = sw*th//sh
            return [('resize', (w, th))]


class ResizeCrop(Resizer):
    '''
    Crops image to the proportion of a given rectange and resizes it
    to the size of the rectangle.

    :param expand: force expand image to the rectangle.

    :param force: force image's proportion to be equal to the rectangle's proportion
    even if source image is smaller in any dimension than target size.
    '''

    def __init__(self, *args, **kwargs):
        self.force = kwargs.pop('force', False)
        Resizer.__init__(self, *args, **kwargs)
        assert not (self.force and self.expand)

    def transformations(self, size, target_size):
        sw, sh = size
        tw, th = target_size
        if not self.expand and not self.force and sw<=tw and sh<=th:
            return []

        if self.force and (sw<=tw or sh<=th):
            if sw*th>sh*tw:
                # crop right and left side
                tw, th = sh*tw//th, sh
            else:
                # crop upper and bottom side
                tw, th = sw, sw*th//tw

        transforms = []
        if sw*th>sh*tw:
            # crop right and left side
            if sh!=th and (sh>th or self.expand):
                w = sw*th//sh
                transforms.append(('resize', (w, th)))
                sw, sh = w, th
            if sw>tw:
                wd = (sw-tw)//2
                transforms.append(('crop', (wd, 0, tw+wd, sh)))
        else:
            # crop upper and bottom side
            if sw!=tw and (sw>tw or self.expand):
                h = sh*tw//sw
                transforms.append(('resize', (tw, h)))
                sw, sh = tw, h
            if sh>th:
                hd = (sh-th)//2
                transforms.append(('crop', (0, hd, sw, th+hd)))
        return transforms


class ResizeMixed(Resizer):

    '''
    Applies one of given rectangles depending on whether the image
    is vertical or horizontal.

    :param rate: multiplier to height to tune a proportion dividing
    horisontal images from verticals. Dy default is equal to 1 (1:1).
    '''

    def __init__(self, hor_resize, vert_resize, rate=1):
        self.hor_resize = hor_resize
        self.vert_resize = vert_resize
        self.rate = rate

    def get_resizer(self, size, target_size):
        '''Choose a resizer depending an image size'''
        sw, sh = size
        if sw >= sh * self.rate:
            return self.hor_resize
        else:
            return self.vert_resize

    def transformations(self, size, target_size):
        return self.get_resizer(size, target_size)\
                   .transformations(size, target_size)

    #def transform(self, img, *args):
    # XXX is this method needed?
    #    return self.get_resizer(img).transform(img, *args)

    def __call__(self, img, target_size):
        return self.get_resizer(img.size, target_size)(img, target_size)


class ResizeFixedWidth(Resizer):

    '''
    Resizes an image to a given width.

    :param expand: force expand image to target size.
    '''

    def transformations(self, size, target_size):
        sw, sh = size
        tw, th = target_size
        if not self.expand and sw<=tw:
            return []
        h = sh*tw//sw
        return [('resize', (tw, h))]


class ResizeFixedHeight(Resizer):

    '''
    Resizes an image to a given height.

    :param expand: force expand image to target size.
    '''

    def transformations(self, size, target_size):
        sw, sh = size
        tw, th = target_size
        if not self.expand and  sh<=th:
            return []
        w = sw*th//sh
        return [('resize', (w, th))]

