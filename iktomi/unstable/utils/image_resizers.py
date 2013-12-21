try:
    import Image
except ImportError:       # pragma: no cover
    from PIL import Image # pragma: no cover


def ResizeFit(expand=False, filter=Image.ANTIALIAS):
    def resize(img, size):
        sw, sh = img.size
        tw, th = size
        if not expand and sw<=tw and sh<=th:
            return img
        if sw*th>sh*tw:
            h = sh*tw//sw
            return img.resize((tw, h), filter)
        else:
            w = sw*th//sh
            return img.resize((w, th), filter)
    return resize


def ResizeCrop(expand=False, filter=Image.ANTIALIAS):
    def resize(img, size):
        sw, sh = img.size
        tw, th = size
        if not expand and sw<=tw and sh<=th:
            return img
        if sw*th>sh*tw:
            if sh!=th and (sh>th or expand):
                w = sw*th//sh
                img = img.resize((w, th), filter)
            sw, sh = img.size
            if sw>tw:
                wd = (sw-tw)//2
                img = img.crop((wd, 0, tw+wd, sh))
        else:
            if sw!=tw and (sw>tw or expand):
                h = sh*tw//sw
                img = img.resize((tw, h), filter)
            sw, sh = img.size
            if sh>th:
                hd = (sh-th)//2
                img = img.crop((0, hd, sw, th+hd))
        return img
    return resize


class ResizeMixed(object):

    def __init__(self, hor_resize, vert_resize):
        self.hor_resize = hor_resize
        self.vert_resize = vert_resize

    def __call__(self, img, size):
        sw, sh = img.size
        if sw >= sh:
            return self.hor_resize(img, size)
        else:
            return self.vert_resize(img, size)


def ResizeFixedWidth(expand=False, filter=Image.ANTIALIAS):
    def resize(img, size):
        sw, sh = img.size
        tw, th = size
        if not expand and sw<=tw:
            return img
        h = sh*tw//sw
        return img.resize((tw, h), filter)
    return resize


def ResizeFixedHeight(expand=False, filter=Image.ANTIALIAS):
    def resize(img, size):
        sw, sh = img.size
        tw, th = size
        if not expand and  sh<=th:
            return img
        w = sw*th//sh
        return img.resize((w, th), filter)
    return resize
