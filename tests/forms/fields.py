# -*- coding: utf-8 -*-
import unittest
from copy import copy

from insanities.forms import fields, convs, form, widgets, media, perms
from insanities.web.core import RequestContext

SAMPLE_FIELD_ARGS = dict(
                        conv=convs.Char,
                        name='input',
                        widget=widgets.TextInput)
SAMPLE_FIELD_ARGS2 = dict(SAMPLE_FIELD_ARGS, name='input2')

SAMPLE_FIELDSET_ARGS = dict(
                        name='fieldset',
                        fields=[
                              fields.Field(**SAMPLE_FIELD_ARGS),
                              fields.Field(**SAMPLE_FIELD_ARGS2)
                            ])

class TestFormClass(unittest.TestCase):
    def setUp(self):
        self.field_args = SAMPLE_FIELD_ARGS.copy()
        self.form_args = {}
        self.fieldset_args = SAMPLE_FIELDSET_ARGS.copy()
        self.fieldset_args['fields'] = copy(self.fieldset_args['fields'])
    
    @property
    def form(self):
        env = self.env
        
        class SampleForm(form.Form):
            fields=[fields.Field(**self.field_args),
                    fields.Field(**SAMPLE_FIELD_ARGS2),
                    fields.FieldSet(**SAMPLE_FIELDSET_ARGS)]
            
        return SampleForm(env, **self.form_args)

    @property
    def env(self):
        from os import path
        import jinja2
        from insanities.ext import jinja2 as jnj

        DIR = jnj.__file__
        DIR = path.dirname(path.abspath(DIR))
        TEMPLATES = [path.join(DIR, 'templates')]
        rctx = RequestContext.blank('/')
        rctx.vals['jinja_env'] = jinja2.Environment(
                            loader=jinja2.FileSystemLoader(TEMPLATES))
        return jnj.FormEnvironment(rctx)

    @property
    def field(self):
        return fields.Field(**self.field_args)
        
    @property
    def fieldset(self):
        return fields.Field(**self.fieldset_args)

class TestField(TestFormClass):
    def check_equality(self, name, arg, arg_or_class):
        if name in ['conv', 'widget']:
            if type(arg) == type(convs.Char):
                # widgets and convs should be instantiated
                assert isinstance(arg, arg_or_class)
            # XXX I don't know how to check if two objects are equal
        else:
            self.assertEqual(arg, arg_or_class)
    
    def test_init(self):
        field1 = self.field
        for key, value in self.field_args.items():
            self.check_equality(key, getattr(field1, key), value)

    def test_bound_field_methods(self):
        # some methods shold be called from field linked to form
        self.assertRaises(fields.FieldError, lambda: self.field.parent)
        self.assertRaises(fields.FieldError, lambda: self.field.form)
        self.assertRaises(fields.FieldError, lambda: self.field.env)
        self.assertRaises(fields.FieldError, lambda: self.field.input_name)
        self.assertRaises(fields.FieldError, lambda: self.field.error)
        self.assertRaises(fields.FieldError, lambda: self.field.value)
        self.assertRaises(fields.FieldError, self.field.accept)
        self.assertRaises(fields.FieldError, lambda: self.field.permissions)
    
    def test_call(self):
        field1 = self.field
        field2 = field1()
        
        for key in SAMPLE_FIELD_ARGS:
            self.check_equality(key, getattr(field1, key), getattr(field2, key))
        
        field2 = field1(name='name')
        self.assertEqual(field1.name, 'input')
        self.assertEqual(field2.name, 'name')

    def test_get_default(self): 
        class SampleForm(form.Form):
            fields=[
                  fields.Field(conv=convs.Int,
                               name='input1',
                               default=10),
                  fields.Field(conv=convs.Int,
                               name='input2'),
                  fields.Field(conv=convs.EnumChoice(multiple=True),
                               name='input3'),
                ]
        
        frm = SampleForm(self.env)
        self.assertEqual(frm.fields[0].get_default(), 10)
        self.assertEqual(frm.fields[1].get_default(), None)
        self.assertEqual(frm.fields[2].get_default(), [])

    def test_perms_from_form(self):
        class SampleForm(form.Form):
            permissions = 'wy'
            fields=[fields.Field('input')]
        
        perm = SampleForm(self.env).fields[0].permissions
        self.assertEqual(perm, set('wy'))
    
    def test_perms_from_getter(self):
        class SampleForm(form.Form):
            permissions = 'rwcx'
            fields=[fields.Field('input',
                                 perm_getter=perms.SimplePerm('rwy'))]
        
        perm = SampleForm(self.env).fields[0].permissions
        self.assertEqual(perm, set('rw'))

    def test_media(self):
        medias = [media.FormJSRef('field_buttons.js'),
                  media.FormCSSRef('field_buttons.ccss'),]

        class SampleForm(form.Form):
            fields=[fields.Field(media=medias, **self.field_args)]
        
        med = SampleForm(self.env).get_media()
        
        for f in medias:
            assert f in med
            
        # Form and Field has no method to render_media, so we can't test it

    def test_accept(self):
        class SampleForm(form.Form):
            fields=[fields.Field(**self.field_args)]

        frm = SampleForm(self.env)
        
        frm.data = form.MultiDict([('input', '12'),])
        field = frm.fields[0]
        field.conv = convs.Char(max_length=3)
        
        self.assertEqual(field.accept(), '12')

    def test_accept_readonly(self):
        class SampleForm(form.Form):
            fields=[fields.Field(conv=convs.Char,
                                 perm_getter=perms.SimplePerm('r'),
                                 name='input')]

        frm = SampleForm(self.env)
        
        frm.data = form.MultiDict([('input', 'somedata'),])
        field = frm.fields[0]

        self.assertRaises(convs.SkipReadonly, field.accept)

    def test_value(self):
        class SampleForm(form.Form):
            fields=[fields.Field(**self.field_args),
                    fields.Field(**SAMPLE_FIELD_ARGS2)]
            
        frm = SampleForm(self.env)
        
        field = frm.get_field('input')
        self.assertEqual(field.value, field.get_default())
        
        frm.accept({'input': '1', 'input2': '2'})
        
        self.assertEqual(frm.get_field('input').value, '1')
        
    def test_fill(self):
        class SampleForm(form.Form):
            fields=[fields.Field(**self.field_args)]
            
        frm = SampleForm(self.env)
        mdict = form.MultiDict()

        field = frm.get_field('input')
        field.fill(mdict, '123')
        self.assertEqual(mdict, form.MultiDict([('input', '123')]))
        
    def test_fill_multiple(self):
        class SampleForm(form.Form):
            fields=[fields.Field(**self.field_args)]
            
        frm = SampleForm(self.env)
        mdict = form.MultiDict()

        field = frm.get_field('input')
        field.conv = convs.EnumChoice(multiple=True)
        field.fill(mdict, ['1', '2', '3'])

        self.assertEqual(mdict, form.MultiDict([
                ('input', '1'), ('input', '2'), ('input', '3')]))
        
        field.fill(mdict, ['5', '6', '7'])
        self.assertEqual(mdict, form.MultiDict([
                ('input', '5'), ('input', '6'), ('input', '7'),
                                               ]))

    def test_error(self):
        class SampleForm(form.Form):
            fields=[
                  fields.Field(name='input1'),
                  fields.Field(name='input2',
                               conv=convs.Int),
                ]

        frm = SampleForm(self.env)
        frm.accept({'input1': '3', 'input2': 'notvalid'})
        assert frm.get_field('input1').error is None
        assert 'integer' in frm.get_field('input2').error

    def test_grab(self):
        class SampleForm(form.Form):
            fields=[fields.Field(**self.field_args)]
            
        frm = SampleForm(self.env)

        # XXX is this test case necessary?
        #frm.data = form.MultiDict([('input', '1'), ('input', '2')])
        frm.data = form.MultiDict([('input', '1')])
        field = frm.get_field('input')

        self.assertEqual(field.grab(), '1')
        
        field.conv = convs.EnumChoice(multiple=True)
        frm.data = form.MultiDict([('input', '1'), ('input', '2')])
        self.assertEqual(field.grab(), ['1', '2'])

    # simple properties
    def test_multiplicity(self):
        field = self.field
        for b in [True, False]:
            field.conv = convs.EnumChoice(multiple=b)
            self.assertEqual(field.multiple, b)
    
    def test_names(self):
        form = self.form
        for name in ['input', 'input2', 'fieldset.input', 'fieldset.input2']:
            field = form.get_field(name)
            self.assertEqual(name, field.input_name)
            self.assertEqual(name.rsplit('.')[-1:][0], field.name)

    def test_form(self):
        form = self.form
        for name in ['input', 'input2', 'fieldset.input', 'fieldset.input2']:
            field = form.get_field('input')
            self.assertEqual(field.form, form)

    def test_parent(self):
        form = self.form
        self.assertEqual(form.fields[0].parent, form)
        
        self.assertRaises(fields.FieldError, lambda: self.field.parent)

    def test_render(self):
        class SampleForm(form.Form):
            fields=[
                  fields.Field(name='input1',
                               widget=widgets.TextInput),
                  fields.Field(name='input2',
                               widget=widgets.TextInput,
                               perm_getter=perms.SimplePerm('r'),
                               default='defaultvalue'),
                ]
        frm = SampleForm(self.env)
        
        # XXX how to assert that it's rendered correctly
        r1 = frm.get_field('input1').render()
        assert "<input " in r1 and "readonly" not in r1

        r2 = frm.get_field('input2').render()
        assert "readonly" in r2 and "defaultvalue" in r2

class TestFieldSet(TestFormClass):

    #def test_predefined_fields(self):
    #    class FSet0(fields.FieldSet):
    #        fields=[fields.Field(conv=convs.Char, name='troll')]
    #
    #    class FList(fields.FieldList):
    #        field = FSet0
    #    
    #    class FSet(fields.FieldSet):
    #        fields = [fields.Field(conv=convs.Char, name='ogre'),
    #                  FList,
    #                  fields.Field]
    #    
    #    fset = FSet('bridge')
    #    x = fset.fields[1].field
    #    assert x.fields[0] is not None

    def test_init_unbound(self):
        fieldset = self.fieldset
        self.assertRaises(fields.FieldError, lambda: fieldset.parent)
        # Assert that descedants of unbound fieldset are unbound
        self.assertRaises(fields.FieldError, lambda: fieldset.fields[0].parent)

    def test_init(self):
        class SampleForm(form.Form):
            fields=[fields.FieldSet(**SAMPLE_FIELDSET_ARGS)]

        fieldset = SampleForm(self.env).fields[0]
        fieldnames = [x.name for x in SAMPLE_FIELDSET_ARGS['fields']]
        for field in fieldset.fields:
            self.assertEqual(field.parent, fieldset)
            assert field.name in fieldnames
        #self.assertEqual(len(fieldset.fields), len(SAMPLE_FIELDSET_ARGS['fields']))
    
    # XXX is it necessary?
    #def test_perms(self):
    #    class SampleForm(form.Form):
    #        permissions = 'rwc'
    #        fields=[fields.FieldSet(name='fieldset',
    #                    perm_getter=perms.SimplePerm('rw'),
    #                    fields=[
    #                          fields.Field('1',
    #                                       perm_getter=perms.SimplePerm('rwx')),
    #                          fields.Field('2',
    #                                       perm_getter=perms.SimplePerm('r'))])
    #               ]
    #    self.assertEqual(field.get_perms(['*']), set('r'))

    def test_value(self):
        class SampleForm(form.Form):
            fields=[fields.FieldSet(name='fieldset',
                                    fields=[
                                          fields.Field(**SAMPLE_FIELD_ARGS),
                                          fields.Field(**SAMPLE_FIELD_ARGS2)])
                   ]

        frm = SampleForm(self.env)
        
        frm.accept({'fieldset.input': '3', 'fieldset.input2': '4'})
        
        self.assertEqual(frm.get_field('fieldset.input').value, '3')
        self.assertEqual(frm.get_field('fieldset').value, {
            'input': '3',
            'input2': '4',
        })

    def test_media(self):
        medias = [media.FormJSRef('field_buttons.js'),
                  media.FormCSSRef('field_buttons.ccss'),]

        class SampleForm(form.Form):
            fields=[fields.FieldSet(
                        name='fieldset',
                        fields=[
                              fields.Field(media=medias[:1], **SAMPLE_FIELD_ARGS),
                              fields.Field(**SAMPLE_FIELD_ARGS2)
                            ])]
            media=medias[1:]
        
        med = SampleForm(self.env).get_media()
        
        for f in medias:
            assert f in med
    
    def test_accept_correct(self):
        class SampleForm(form.Form):
            fields=[fields.FieldSet(
                        name='fieldset',
                        fields=[
                              fields.Field(conv=convs.Int,
                                           name='input',
                                           default=10),
                            ])]
        
        frm = SampleForm(self.env)
        assert frm.accept(form.MultiDict([('fieldset.input', '12'),]))

        fieldset = frm.fields[0]
        self.assertEqual(fieldset.value, {'input': 12})

    def test_accept_readonly(self):
        class SampleForm(form.Form):
            fields=[fields.FieldSet(
                        name='fieldset',
                        fields=[
                              fields.Field(name='input1',
                                           default='10',
                                           permissions=''),
                              fields.Field(name='input2',
                                           default=12,
                                           permissions='',
                                           conv=convs.Int),
                              fields.Field(name='input3'),
                            ])]
        
        frm = SampleForm(self.env)
        assert frm.accept(form.MultiDict([
                    ('fieldset.input1', '12'),
                    ('fieldset.input2', '20'),
                    ('fieldset.input3', '20'),
                    ]))
        fieldset = frm.fields[0]
        self.assertEqual(fieldset.python_data,
                         {'input1': '10',
                          'input2': 12,
                          'input3': '20'
                         })
        
    def test_errors_in_readonly(self): pass
    # XXX to be written
        # readonly value that doesn't validate
        #assert fieldset.get_field('input2').error

    def test_accept_nested(self):
        class SampleForm(form.Form):
            fields=[fields.FieldSet(
                        name='fieldset',
                        fields=[
                              fields.Field(name='input1'),
                              fields.FieldSet(
                                    name='fieldset2',
                                    fields=[
                                        fields.Field(
                                            conv=convs.Int,
                                            name='input1'),
                                        fields.Field(name='input2'),
                                        ]),
                              fields.Field(name='input2'),
                            ])]
        
        frm = SampleForm(self.env)
        frm.data = form.MultiDict([
            ('fieldset.input1', '12'),
            ('fieldset.input2', '20'),
            ('fieldset.fieldset2.input1', 'word'),
            ('fieldset.fieldset2.input2', '20'),
            ])
        fieldset = frm.fields[0]
        self.assertRaises(convs.NestedError, fieldset.accept)

    def test_accept_notvalid(self):
        class SampleForm(form.Form):
            fields=[fields.FieldSet(
                        name='fieldset',
                        fields=[
                              fields.Field(conv=convs.Int,
                                           name='input',
                                           default=10),
                              fields.Field(conv=convs.Int,
                                           name='valid',
                                           default=12),
                            ])]
        
        frm = SampleForm(self.env)
        frm.data = form.MultiDict([
            ('fieldset.input', 'word'),
            ('fieldset.valid', '20'),
            ])
        fieldset = frm.fields[0]
        self.assertRaises(convs.NestedError, fieldset.accept)

        # FieldSet doesn't modify anything if one of fields is invalid
        # see http://bitbucket.org/riffm/insanities-testing/issue/5/
        self.assertEqual(fieldset.python_data, {'input': 10, 'valid': 12})
    
    def test_get_default(self): 
        class SampleForm(form.Form):
            fields=[fields.FieldSet(
                        name='fieldset',
                        fields=[
                              fields.Field(conv=convs.Int,
                                           name='input1',
                                           default=10),
                              fields.Field(conv=convs.Int,
                                           name='input2')
                            ])]
        
        default = SampleForm(self.env).fields[0].get_default()
        self.assertEqual(default, {'input2': None, 'input1': 10})

    def test_get_default_validation(self):
        class SampleConverter(convs.Converter):
            def to_python(self, value):
                if value['input1'] == value['input2']:
                    raise convs.ValidationError("I don't like this value")
                return value
        
        class SampleForm(form.Form):
            fields=[fields.FieldSet(
                        conv=SampleConverter,
                        name='fieldset',
                        fields=[
                              fields.Field(conv=convs.Int,
                                           name='input1',
                                           default=10),
                              fields.Field(conv=convs.Int,
                                           name='input2',
                                           default=10)
                            ])]
        
        # If validation on default value fails, get_default should raise an Error
        # It should be tested on Form initialization
        self.assertRaises(AssertionError, SampleForm, self.env)
    
    def test_get_field(self):
        class SampleForm(form.Form):
            fields=[fields.FieldSet(
                        name='fieldset',
                        fields=[
                              fields.Field(name='input1'),
                              fields.FieldSet(
                                    name='input2',
                                    fields=[fields.Field(name='input3')])
                            ])]
        
        fieldset = SampleForm(self.env).fields[0]
        
        self.assertEqual(fieldset.get_field('input1').name, 'input1')
        self.assertEqual(fieldset.get_field('input2.input3').name, 'input3')
        self.assertEqual(fieldset.get_field('input4'), None)
        

    def test_fill(self):
        class SampleForm(form.Form):
            fields=[fields.FieldSet(
                        name='fieldset',
                        fields=[
                              fields.Field(**SAMPLE_FIELD_ARGS),
                              fields.Field(**SAMPLE_FIELD_ARGS2)
                            ])]
            
        frm = SampleForm(self.env)
        mdict = form.MultiDict()

        frm.fields[0].fill(mdict, {
            'input': '1',
            'input2': '2'
        })
        self.assertEqual(mdict, form.MultiDict([
            ('fieldset.input', '1'), ('fieldset.input2', '2'),
        ]))
    
    # XXX what if there are two FieldSets with similar fields?

class FieldList(TestFormClass):

    def test_init_unbound(self):
        fieldlist=fields.FieldList(name='list',
                                   field=fields.Field(None))
        self.assertRaises(fields.FieldError, lambda: fieldlist.parent)
        # Assert that descedants of unbound fieldlist is unbound
        self.assertRaises(fields.FieldError, lambda: fieldlist.field.parent)

    def test_init(self):
        class SampleForm(form.Form):
            fields=[fields.FieldList(name='list',
                                     field=fields.Field(None))]

        fieldlist = SampleForm(self.env).fields[0]
        self.assertEqual(fieldlist.field.parent, fieldlist)

    def test_get_field(self):
        class SampleForm(form.Form):
            fields=[fields.FieldList(name='list1',
                                     field=fields.Field(name='field')),
                    fields.FieldList(name='list2',
                                     field=fields.Field(None)),
                    ]
        
        frm = SampleForm(self.env)
        self.assertEqual(frm.get_field('list1.field').name, 'field')
        self.assertEqual(frm.get_field('list1.abyr'), None)
        self.assertEqual(frm.get_field('list2.abyr').name, None)

    def test_accept(self):
        class SampleForm(form.Form):
            fields=[fields.FieldList(name='list',
                                     field=fields.Field(name='field')),
                    ]

        frm = SampleForm(self.env)
        fieldlist = frm.fields[0]
        
        mdict = form.MultiDict([(fieldlist.indeces_input_name, 1),
                                (fieldlist.indeces_input_name, 2),
                                ('list-1', 'word'),
                                ('list-2', 'secondword'),
                               ])
        frm.accept(mdict)
        
        self.assertEqual(fieldlist.value, ['word', 'secondword'])

    def test_accept(self):
        class SampleForm(form.Form):
            fields=[fields.FieldList(name='list',
                                     field=fields.Field(name='field')),
                    ]

        frm = SampleForm(self.env)
        fieldlist = frm.fields[0]
        
        mdict = form.MultiDict([(fieldlist.indeces_input_name, 1),
                                (fieldlist.indeces_input_name, 2),
                                ('list-1', 'word'),
                                ('list-2', 'secondword'),
                               ])
        frm.accept(mdict)
        
        self.assertEqual(fieldlist.value, ['word', 'secondword'])

    def test_accept_notvalid(self):
        class SampleForm(form.Form):
            fields=[fields.FieldList(name='list',
                                     field=fields.Field(name='field',
                                                        conv=convs.Int)),
                    ]

        frm = SampleForm(self.env)
        fieldlist = frm.fields[0]
        
        mdict = form.MultiDict([(fieldlist.indeces_input_name, 1),
                                (fieldlist.indeces_input_name, 2),
                                ('list-1', '123'),
                                ('list-2', 'secondword'),
                               ])
        assert not frm.accept(mdict)
        
        # FieldList doesn't modify anything if one of fields is invalid
        # see http://bitbucket.org/riffm/insanities-testing/issue/5/
        self.assertEqual(fieldlist.value, [])

    def test_fill(self):
        class SampleForm(form.Form):
            fields=[fields.FieldList(name='list',
                                     field=fields.Field(name='field')),
                    ]

        frm = SampleForm(self.env)
        fieldlist = frm.fields[0]
        
        mdict = form.MultiDict([('list-1', 'word'),
                                ('list-2', 'secondword'),
                                (fieldlist.indeces_input_name, '1'),
                                (fieldlist.indeces_input_name, '2'),
                               ])
        
        mdict2 = form.MultiDict([])
        fieldlist.fill(mdict2, {'1': 'word', '2': 'secondword'})
        self.assertEqual(mdict, mdict2)
    #def test_render(self): pass
    #def get_media(self): pass

if __name__ == '__main__':
    unittest.main()
