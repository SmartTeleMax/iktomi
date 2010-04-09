# -*- coding: utf-8 -*-
import unittest
from insanities.forms import convs
from insanities.utils.odict import OrderedDict

class TestConv(unittest.TestCase):
    
    def test_multiplicity(self):
        pass
    
    def test_chaining(self):
        pass
    
    def test_messages(self):
        pass

class TestChar(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_clean_any_value(self):
        txt = 'any random value'
        clean = convs.Char().to_python(txt)
        self.assertEqual(clean, txt)

    def test_min_max(self):
        conv = convs.Char(min_length=2, max_length=5)
        
        self.assertRaises(convs.ValidationError, conv.to_python, 'a')
        self.assertRaises(convs.ValidationError, conv.to_python, 'abcdef')
        self.assertEqual(conv.to_python('abcde'), 'abcde')
        self.assertEqual(conv.to_python('ab'), 'ab')

    def test_regex(self):
        conv = convs.Char(regex="\d+")
        
        self.assertRaises(convs.ValidationError, conv.to_python, 'a32')
        self.assertEqual(conv.to_python('32'), '32')


class TestInt(unittest.TestCase):
    
    def test_clean_any_value(self):
        conv = convs.Int()
        self.assertEqual(conv.to_python('1'), 1)
        self.assertEqual(conv.to_python('0'), 0)
        self.assertRaises(convs.ValidationError, conv.to_python, 'a12')

    def test_min_max(self):
        conv = convs.Int(min=2, max=5)
        
        self.assertRaises(convs.ValidationError, conv.to_python, 1)
        self.assertRaises(convs.ValidationError, conv.to_python, 6)
        self.assertEqual(conv.to_python(5), 5)
        self.assertEqual(conv.to_python(2), 2)

 
    def test_call(self):
        conv = convs.Int(min=2, max=5, null=True)()

        self.assertEqual(conv.min, 2)
        self.assertEqual(conv.max, 5)
        self.assertEqual(conv.null, True)

    def test_from_python(self):
        conv = convs.Int()
        self.assertEqual(conv.from_python(None), '')
        self.assertEqual(conv.from_python(0), '0')


class TestBool(unittest.TestCase):
    
    def test_clean_any_value(self):
        conv = convs.Bool()
        self.assertEqual(conv.to_python('1'), True)
        self.assertEqual(conv.to_python(''), False)

    def test_from_python(self):
        conv = convs.Bool()
        self.assertEqual(conv.from_python(False), '')
        self.assertEqual(conv.from_python(True), 'checked')


class TestDisplayOnly(unittest.TestCase):
    
    def test_clean_any_value(self):
        conv = convs.DisplayOnly()
        self.assertRaises(convs.SkipReadonly, conv.to_python, '')

    def test_from_python(self):
        conv = convs.DisplayOnly()
        # XXX is it right?
        self.assertEqual(conv.from_python(1), 1)
        self.assertEqual(conv.from_python('checked'), 'checked')

    
class TestEnumChoice(unittest.TestCase):
    
    def test_clean_single(self):
        conv = convs.EnumChoice(choices=[
                                    (0, 'label_0'),
                                    (1, 'label_1'),
                                ],
                                multiple=False,
                                null=True,
                                conv=convs.Int())
        self.assertEqual(conv.to_python('0'), 0)
        self.assertEqual(conv.to_python('3'), None)

        conv = convs.EnumChoice(choices=[
                                    (0, 'label_0'),
                                    (1, 'label_1'),
                                ],
                                multiple=False,
                                null=False,
                                conv=convs.Int())
        self.assertRaises(convs.ValidationError, conv.to_python, '3')

    def test_clean_multiple(self):
        conv = convs.EnumChoice(choices=[
                                    (0, 'label_0'),
                                    (1, 'label_1'),
                                ],
                                multiple=True,
                                null=True,
                                conv=convs.Int())
        self.assertEqual(conv.to_python(['0', '1']), [0, 1])
        self.assertEqual(conv.to_python(['0', '3']), [0])
        self.assertEqual(conv.to_python(['3']), [])

        conv = convs.EnumChoice(choices=[
                                    (0, 'label_0'),
                                    (1, 'label_1'),
                                ],
                                multiple=True,
                                null=False,
                                conv=convs.Int())
        self.assertRaises(convs.ValidationError, conv.to_python, ['3'])

    def test_iter(self):
        conv = convs.EnumChoice(choices=[
                                    (0, 'label_0'),
                                    (1, 'label_1'),
                                ],
                                conv=convs.Int())
        lst = [x for x in conv]
        
        self.assertEqual(lst, [('0', 'label_0'), ('1', 'label_1')])

    def test_get_label(self):
        conv = convs.EnumChoice(choices=[
                                    (0, 'label_0'),
                                    (1, 'label_1'),
                                ],
                                conv=convs.Int())
        # XXX '0' or 0? Should passed value be cleaned or not?
        self.assertEqual(conv.get_label('0'), 'label_0')

    def test_from_python(self):
        conv = convs.EnumChoice(choices=[
                                    (0, 'label_0'),
                                    (1, 'label_1'),
                                ],
                                multiple=True,
                                conv=convs.Int())
        #self.assertEqual(conv.from_python([0, 1, 2]), ['0', '1'])
        self.assertEqual(conv.from_python([0, 1]), ['0', '1'])
        
        conv.multiple = False
        self.assertEqual(conv.from_python(0), '0')


# XXX DATE CONVERTERS!
    
class TestHtml(unittest.TestCase):
    '''Tests for html converter'''

    def setUp(self):
        self.conv_class = convs.Html
        self.attrs = {
            'allowed_elements': ('a', 'p'),
            'allowed_attributes': ('title', 'href'),
        }
    @property
    def conv(self):
        return self.conv_class(**self.attrs)

    def assertEqualSets(self, a, b):
        return self.assertEqual(set(a), set(b))

    def test_setting(self):
        '''Ensure that values are setted correctly'''
        conv = self.conv
        self.assertEqualSets(conv.tags, ['a', 'p'])

    def test_double_setting(self):
        '''Ensure that values are passed correctly in __call__ method'''
        conv = self.conv()
        self.assertEqualSets(conv.tags, ['a', 'p'])
    
    def test_adding(self):
        '''Ensure that adding works properly'''
        conv = self.conv(add_allowed_elements=['span'])
        self.assertEqualSets(conv.tags, ['a', 'p', 'span'])
    
        conv = self.conv(add_allowed_elements=['span'])(add_allowed_elements=['b'])
        self.assertEqualSets(conv.tags, ['a', 'p', 'b', 'span'])

        conv = self.conv(add_string_callbacks=[1])
        from insanities.utils.html import Sanitizer
        self.assertEqual(len(conv._init_kwargs['string_callbacks']),
                         len(Sanitizer.string_callbacks) + 1)
    
    def test_adding_independence(self):
        '''Ensure that adding has no side effects on source converter'''
        conv = self.conv
        conv1 = conv(add_allowed_elements=['b'])
        conv2 = conv(add_allowed_elements=['span'])

        self.assertEqualSets(conv1.tags, ['a', 'p', 'b'])
        self.assertEqualSets(conv2.tags, ['a', 'p', 'span'])
        self.assertEqualSets(conv.tags, ['a', 'p'])

    def test_empty_attrs(self):
        '''Ensure that default values are setted correctly'''
        self.attrs = {}
        assert len(self.conv.tags) > 0
    
    def test_inheritance(self):
        '''Ensure that inheritance works properly'''
        class HtmlInherited(convs.Html):
            allowed_classes = { 'a': ['cls'] }
            allowed_elements = ('a', 'p')
            add_allowed_attributes = ('src',)
        
        conv = HtmlInherited(allowed_attributes=('title', 'href'))
        self.assertEqual(conv.allowed_classes, { 'a': ['cls'] })
        self.assertEqualSets(conv.tags, ('a', 'p'))
        # passed kwarg should be stronger that `add` property declared in class
        self.assertEqualSets(conv.attrs, ('title', 'href')) 

        class HtmlInherited(convs.Html):
            allowed_elements = ('a', 'p')
            add_allowed_elements = ('span',)
            
        conv = HtmlInherited()
        self.assertEqualSets(conv.tags, ('a', 'span', 'p'))


class TestList(unittest.TestCase):
    
    def test_clean(self):
        conv = convs.List()
        odict = OrderedDict({1: 1})
        odict[0] = 0
        
        self.assertEqual(conv.to_python(odict), [1, 0])
        
        odict.sort()
        self.assertEqual(conv.to_python(odict), [0, 1])
        
    def test_filter(self):
        conv = convs.List(filter=lambda x: x)
        odict = OrderedDict({1: 1, 2:2, 0:0})
        
        self.assertEqual(conv.to_python(odict), [1, 2])
        
    def test_min_max(self):
        conv = convs.List(min_length=2, max_length=4)
        
        odict = OrderedDict({1: 1})
        self.assertRaises(convs.ValidationError, conv.to_python, odict)
        odict = OrderedDict({1: 1, 2: 2, 3: 3, 4: 4, 5: 5})
        self.assertRaises(convs.ValidationError, conv.to_python, odict)

        odict = OrderedDict({1: 1, 2: 2, 3: 3, 4: 4})
        self.assertEqual(conv.to_python(odict), [1, 2, 3, 4])
        odict = OrderedDict({1: 1, 2: 2})
        self.assertEqual(conv.to_python(odict), [1, 2])

    def test_from_python(self):
        conv = convs.List()
        
        # XXX why not {1: 'first', 2: 'second'} ?
        odict = OrderedDict({'1': 'first', '2': 'second'})
        self.assertEqual(conv.from_python(['first', 'second']), odict)


if __name__ == '__main__':
    unittest.main()
