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

    def checkResize(self, resizer, size, target, result):
        self.assertEqual(resizer(img(*size), target).size, result)
        self.assertEqual(resizer.get_target_size(size, target), result)

    def test_resize_fit(self):
        check = self.checkResize
        check(ResizeFit(), (50, 50), (5, 5), (5, 5))
        check(ResizeFit(), (50, 30), (5, 5), (5, 3))
        check(ResizeFit(), (30, 50), (5, 5), (3, 5))
        check(ResizeFit(), (3, 5), (50, 50), (3, 5))
        check(ResizeFit(expand=True), (3, 5), (50, 50), (30, 50))

    def test_resize_crop(self):
        check = self.checkResize
        check(ResizeCrop(), (50, 50), (5, 5), (5, 5))
        check(ResizeCrop(), (50, 30), (5, 4), (5, 4))
        check(ResizeCrop(), (30, 50), (5, 4), (5, 4))
        check(ResizeCrop(), (30, 50), (40, 40), (30, 40))
        check(ResizeCrop(), (3, 5), (50, 50), (3, 5))
        check(ResizeCrop(expand=True), (3, 5), (50, 50), (50, 50))

    def test_resize_crop_force(self):
        check = self.checkResize
        check(ResizeCrop(force=True), (50, 50), (5, 5), (5, 5))
        check(ResizeCrop(force=True), (50, 30), (5, 4), (5, 4))
        check(ResizeCrop(force=True), (30, 50), (5, 4), (5, 4))
        check(ResizeCrop(force=True), (30, 50), (40, 40), (30, 30))
        check(ResizeCrop(force=True), (3, 5), (50, 50), (3, 3))
        check(ResizeCrop(force=True), (5, 3), (50, 50), (3, 3))
        self.assertRaises(AssertionError, ResizeCropforce=True, expand=True)

    def test_resize_mixed(self):
        check = self.checkResize
        resize = ResizeMixed(ResizeFit(), ResizeCrop())
        check(resize, (50, 30), (5, 4), (5, 3))
        check(resize, (30, 50), (4, 5), (4, 5))

        resize = ResizeMixed(ResizeFit(), ResizeCrop(), rate=2)
        check(resize, (50, 30), (5, 4), (5, 4))
        check(resize, (50, 20), (5, 4), (5, 2))

    def test_resize_fixed_width(self):
        check = self.checkResize
        RFW = ResizeFixedWidth
        check(RFW(), (50, 50), (5, 5), (5, 5))
        check(RFW(), (50, 30), (5, 5), (5, 3))
        check(RFW(), (10, 20), (5, 5), (5, 10))
        check(RFW(), (5, 10), (50, 50), (5, 10))
        check(RFW(expand=True), (5, 10), (50, 50), (50, 100))

    def test_resize_fixed_height(self):
        check = self.checkResize
        RFH = ResizeFixedHeight
        check(RFH(), (50, 50), (5, 5), (5, 5))
        check(RFH(), (30, 50), (5, 5), (3, 5))
        check(RFH(), (20, 10), (5, 5), (10, 5))
        check(RFH(), (10, 5), (50, 50), (10, 5))
        check(RFH(expand=True), (10, 5), (50, 50), (100, 50))


