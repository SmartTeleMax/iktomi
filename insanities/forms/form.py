# -*- coding: utf-8 -*-

from time import time
import struct, os, itertools
from gettext import NullTranslations

from webob.multidict import MultiDict
from ..utils import weakproxy, cached_property
from ..utils.i18n import smart_gettext

from . import convs
from .perms import DEFAULT_PERMISSIONS
from .media import FormMedia


class BaseFormEnvironment(object):
    '''
    Mixin adding get_string method to environment
    '''

    def __init__(self, rctx=None):
        '''
            Should be implemented in subclasses.
            The only claim is to put rctx into self.rctx
        '''
        self.rctx = rctx

    def render(self, template, form):
        '''Should be implemented in subclasses'''
        raise NotImplementedError()

    @cached_property
    def translation(self):
        return self.rctx.vals.get('translation', NullTranslations())

    def gettext(self, msg, count=None):
        '''Smart gettext method. If the given message is instance of
        :class:`M_ <insanities.utils.i18.M_>` subclass, returns a plural
        form of message translation. Otherwhise, returns single form.

        Can be overriden in subclasses (f.e. to use babel instead of gettext)'''
        return smart_gettext(self.translation, msg, count=None)

    def ngettext(self, single, plural, count):
        '''A proxy method to gettext ungettext method.
        Can be overriden in subclasses (f.e. to use babel instead of gettext)'''
        return self.translation.ungettext(single, plural, count)


class Form(object):

    '''
    Object designed to validate and convert data passed throught HTTP

    To use it you must specify an ancestor class, like this::

        class MyForm(Form):
            fields=[
                  fields.Field(name='input2',
                               conv=convs.Int,
                               widget=widgets.TextInput),
                ]
            template = 'form-template'
            medias = [media.FormJSRef('field_buttons.js'),
                      media.FormCSSRef('field_buttons.css'),]
            permissions = 'rw'

    The constructor accepts folowing parameters:

    :*env* - FormEnvironment instance, which keeps usefull stuff.
    There is only one required method to be implemented in FormEnvironment:
    FormEnvironment.render(template_name, **kwargs)

    :*initial* - dictionary containing initial data for the form.

    :*name* - name of the form. Used asname attribute of form HTML tag,
    as a part of form's inputs names.

    :*permissions* - an iterable containing all allowed permissions for
    this particular form.
    '''

    template = 'table'
    media = FormMedia()
    permissions = DEFAULT_PERMISSIONS

    def __init__(self, env, initial={}, name=None, permissions=None):
        self.env = env
        self.name = name
        self.data = data = MultiDict()
        self.initial = initial
        self.python_data = initial.copy()
        # clone all fields
        self.fields = [field(parent=self) for field in self.fields]

        if permissions is None:
            # to allow permissions definition in Form class
            permissions = self.permissions
        self.permissions = set(permissions)

        for field in self.fields:
            if field.name in initial:
                value = initial[field.name]
            else:
                # get_default() may return different values for each call, so
                # we have to insure converted value match python one.
                value = field.get_default()
            self.python_data[field.name] = value
            field.fill(self.data, field.from_python(value))
        self.errors = {}

    @cached_property
    def id(self):
        '''Random ID for given form input'''
        # Time part is repeated in about 3 days period
        time_part = struct.pack('!d', time())[3:]
        return (time_part+os.urandom(1)).encode('hex')

    def get_data(self, compact=True):
        '''
        Fills form data into new MultiDict.

        If compact is True, includes only not-None values
        '''
        data = MultiDict()
        for field in self.fields:
            field.fill(data, field.from_python(self.python_data[field.name]))
        if compact:
            compact_data = MultiDict()
            for key in data:
                values = filter(None, data.getall(key))
                if values:
                    for v in values:
                        compact_data.add(key, v)
            data = compact_data
        return data

    @property
    def form(self):
        return self

    @property
    def prefix(self):
        '''A prefix for names of field inputs'''
        if self.name:
            return self.name+':'
        else:
            return ''

    def render(self):
        '''Proxy method to form's environment render method'''
        return self.env.render('forms/'+self.template, form=self)

    @property
    def is_valid(self):
        '''Is true if validated form as no errors'''
        return not self.errors

    def get_media(self):
        '''
        Returns a list of FormMedia objects related to the form and
        all of it's fields
        '''
        media = FormMedia(self.media, env=self.env)
        for field in self.fields:
            media += field.get_media()
        return media

    def accept(self, data, files=None):
        '''
        Takes data (usually, request.POST) MultiDict and optionally files
        MultiDict. Validates given data using form's fields' accept method.
        If there are validation errors, collects them for future display.

        If particular field has no edit permissions, disallows it's editing.

        Provides an additional interface for field validation using form's
        :meth:`clean__%s` methods. This tests are started after accepting all
        of fields' data. This interface is useful for validation of couple of
        fields. Here is example it's of usage::

            class MyForm(form.Form):
                def clean__fieldname(self, value):
                    othervalue = self.python_data['otherfield']
                    if not mytest(value, othervalue):
                        raise convs.ValidationError("I don't like it")
                    return value

        Returns True if the form is valid
        '''
        self.data = MultiDict(data)
        self.files = files or MultiDict()
        self.errors = {}
        for field in self.fields:
            try:
                self.python_data[field.name] = field.accept()
            except convs.ValidationError, e:
                self.errors[field.input_name] = e.message
            except convs.NestedError:
                pass
            except convs.SkipReadonly:
                field.fill(self.data,
                           field.from_python(self.python_data[field.name]))
                try:
                    if hasattr(field, 'grab'):
                        field.to_python(field.grab())
                except convs.ValidationError, e:
                    self.errors[field.input_name] = e.message
                except convs.NotSubmitted:
                    pass

        if not self.is_valid:
            return False

        for field in self.fields:
            validate = getattr(self, 'clean__%s' % field.name, None)
            if validate:
                try:
                    self.python_data[field.name] = \
                        validate(self.python_data.get(field.name, None))
                except convs.ValidationError, e:
                    self.errors[field.input_name] = e.message
                    del self.python_data[field.name]

        return self.is_valid

    def get_field(self, name):
        '''
        Gets field by input name
        '''
        names = name.split('.', 1)
        for field in self.fields:
            if field.name == names[0]:
                if len(names) > 1:
                    return field.get_field(names[1])
                return field
        return None
