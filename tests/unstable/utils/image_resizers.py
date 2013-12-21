# -*- coding: utf-8 -*-
from random import randint

__all__ = ['ReverseTests', 'LocationsTests']

import unittest
from iktomi.unstable.utils.image_resizers import ResizeFit, ResizeCrop, \
        ResizeMixed, ResizeFixedHeight, ResizeFixedWidth
try:
    from PIL import Image
except ImportError:
    import Image


def img(width, height):
    image = Image.new('RGB', (width, height), (randint(1, 240),
                                               randint(1, 240),
                                               randint(1, 240), 1))
    return image

class ResizersTests(unittest.TestCase):

    def test_resize_fit(self):
        eq = self.assertEqual
        eq(ResizeFit()(img(50, 50), (5, 5)).size, (5, 5))
        eq(ResizeFit()(img(50, 30), (5, 5)).size, (5, 3))
        eq(ResizeFit()(img(30, 50), (5, 5)).size, (3, 5))
        eq(ResizeFit()(img(3, 5), (50, 50)).size, (3, 5))
        eq(ResizeFit(expand=True)(img(3, 5), (50, 50)).size, (30, 50))

    def test_resize_crop(self):
        eq = self.assertEqual
        eq(ResizeCrop()(img(50, 50), (5, 5)).size, (5, 5))
        eq(ResizeCrop()(img(50, 30), (5, 4)).size, (5, 4))
        eq(ResizeCrop()(img(30, 50), (5, 4)).size, (5, 4))
        eq(ResizeCrop()(img(30, 50), (40, 40)).size, (30, 40))
        eq(ResizeCrop()(img(3, 5), (50, 50)).size, (3, 5))
        eq(ResizeCrop(expand=True)(img(3, 5), (50, 50)).size, (50, 50))

    def test_resize_mixed(self):
        eq = self.assertEqual
        resize = ResizeMixed(ResizeFit(), ResizeCrop())
        eq(resize(img(50, 30), (5, 4)).size, (5, 3))
        eq(resize(img(30, 50), (4, 5)).size, (4, 5))

    def test_resize_fixed_width(self):
        eq = self.assertEqual
        RFW = ResizeFixedWidth
        eq(RFW()(img(50, 50), (5, 5)).size, (5, 5))
        eq(RFW()(img(50, 30), (5, 5)).size, (5, 3))
        eq(RFW()(img(10, 20), (5, 5)).size, (5, 10))
        eq(RFW()(img(5, 10), (50, 50)).size, (5, 10))
        eq(RFW(expand=True)(img(5, 10), (50, 50)).size, (50, 100))

    def test_resize_fixed_height(self):
        eq = self.assertEqual
        RFH = ResizeFixedHeight
        eq(RFH()(img(50, 50), (5, 5)).size, (5, 5))
        eq(RFH()(img(30, 50), (5, 5)).size, (3, 5))
        eq(RFH()(img(20, 10), (5, 5)).size, (10, 5))
        eq(RFH()(img(10, 5), (50, 50)).size, (10, 5))
        eq(RFH(expand=True)(img(10, 5), (50, 50)).size, (100, 50))


