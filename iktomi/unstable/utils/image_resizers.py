try:
    import Image
except ImportError:       # pragma: no cover
    from PIL import Image # pragma: no cover


class Resizer(object):

    def __init__(self, expand=False, filter=Image.ANTIALIAS):
        self.expand = expand
        self.filter = filter

    def transformations(self, img, target_size):
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

    def __call__(self, img, target_size):
        transforms = self.transformations(img, target_size)
        for transformation, params in transforms:
            img = self.transform(img, transformation, params)
        return img


class ResizeFit(Resizer):

    def transformations(self, img, target_size):
        sw, sh = img.size
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

    def transformations(self, img, target_size):
        sw, sh = img.size
        tw, th = target_size
        if not self.expand and sw<=tw and sh<=th:
            return []

        transforms = []
        if sw*th>sh*tw:
            if sh!=th and (sh>th or self.expand):
                w = sw*th//sh
                transforms.append(('resize', (w, th)))
                sw, sh = w, th
            if sw>tw:
                wd = (sw-tw)//2
                transforms.append(('crop', (wd, 0, tw+wd, sh)))
        else:
            if sw!=tw and (sw>tw or self.expand):
                h = sh*tw//sw
                transforms.append(('resize', (tw, h)))
                sw, sh = tw, h
            if sh>th:
                hd = (sh-th)//2
                transforms.append(('crop', (0, hd, sw, th+hd)))
        return transforms


class ResizeMixed(Resizer):

    def __init__(self, hor_resize, vert_resize):
        self.hor_resize = hor_resize
        self.vert_resize = vert_resize

    def get_resizer(self, img, target_size):
        sw, sh = img.size
        if sw >= sh:
            return self.hor_resize
        else:
            return self.vert_resize

    def transformations(self, img, size):
        return self.get_resizer(img, size).transformations(img, size)

    #def transform(self, img, *args):
    # XXX is this method needed?
    #    return self.get_resizer(img).transform(img, *args)

    def __call__(self, img, size):
        return self.get_resizer(img, size)(img, size)


class ResizeFixedWidth(Resizer):
    def transformations(self, img, target_size):
        sw, sh = img.size
        tw, th = target_size
        if not self.expand and sw<=tw:
            return []
        h = sh*tw//sw
        return [('resize', (tw, h))]


class ResizeFixedHeight(Resizer):

    def transformations(self, img, target_size):
        sw, sh = img.size
        tw, th = target_size
        if not self.expand and  sh<=th:
            return []
        w = sw*th//sh
        return [('resize', (w, th))]
