from PIL import Image


class Resizer(object):

    def __init__(self, expand=False, filter=Image.ANTIALIAS):
        self.expand = expand
        self.filter = filter

    def transformations(self, size, target_size):
        # should return a list of JSON-serializable commands
        # that are processed with transform method
        raise NotImplementedError

    def transform(self, img, transformation, params):
        # transformations MUST be idempotent
        if transformation == 'crop':
            return img.crop(params)
        elif transformation == 'resize':
            return img.resize(params, self.filter)
        else:
            raise NotImplementedError(transformation)

    def get_target_size(self, size, target_size):
        transforms = self.transformations(size, target_size)
        for transformation, params in transforms:
            if transformation == 'resize':
                size = params
            elif transformation == 'crop':
                size = (params[2] - params[0], params[3] - params[1])
            else:
                raise NotImplementedError(transformation)
        return size

    def __call__(self, img, target_size):
        transforms = self.transformations(img.size, target_size)
        for transformation, params in transforms:
            img = self.transform(img, transformation, params)
        return img


class ResizeFit(Resizer):

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

    def __init__(self, hor_resize, vert_resize, rate=1):
        self.hor_resize = hor_resize
        self.vert_resize = vert_resize
        self.rate = rate

    def get_resizer(self, size, target_size):
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

    def transformations(self, size, target_size):
        sw, sh = size
        tw, th = target_size
        if not self.expand and sw<=tw:
            return []
        h = sh*tw//sw
        return [('resize', (tw, h))]


class ResizeFixedHeight(Resizer):

    def transformations(self, size, target_size):
        sw, sh = size
        tw, th = target_size
        if not self.expand and  sh<=th:
            return []
        w = sw*th//sh
        return [('resize', (w, th))]

