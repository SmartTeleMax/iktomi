import six
from iktomi.utils import cached_property
from iktomi.unstable.utils.functools import return_locals


class ModelFactories(object):

    def __init__(self):
        self.models = []
        self.i18n_models = []

    def get_constructor(self, func):
        return return_locals(func)

    def register(self, *base_names, **kwargs):
        lang = kwargs.pop('lang', False)
        langs = kwargs.pop('langs', None)
        assert not kwargs
        def decor(func):
            name = func.__name__
            constructor = self.get_constructor(func)
            if lang:
                self.i18n_models.append((name, constructor, base_names, langs))
            else:
                self.models.append((name, constructor, base_names))
            return constructor
        return decor

    def create_model(self, module, name, constructor, base_names):
        values = constructor(ModelsProxy(module, self))
        values['models'] = module
        return self.make_class(module, name, base_names, values)

    def make_class(self, module, name, base_names, values):
        is_string = lambda x: isinstance(x, six.string_types)

        bases = tuple(getattr(module, x) if is_string(x) else x
                      for x in base_names)
        cls = type(name, bases, values)
        cls.__module__ = module.__name__
        return cls

    def create_all(self, module, all_lang_modules=(), model_names=None):
        for name, constructor, base_names in self.models:
            if hasattr(module, name):
                continue
            if model_names is not None and name not in model_names:
                continue
            cls = self.create_model(module, name, constructor, base_names)
            setattr(module, name, cls)

        all_langs = [x.lang for x in all_lang_modules]
        for name, constructor, base_names, langs in self.i18n_models:
            if model_names is not None and name not in model_names:
                continue
            if langs is None:
                lang_modules = all_lang_modules
                langs = list(all_langs)
            else:
                lang_modules = [getattr(module, l) for l in langs]
            for lang_module in lang_modules:
                lang_name = lang_module._get_model_name(name)
                if hasattr(module, lang_name):
                    continue
                cls = self.create_model(lang_module, lang_name,
                                        constructor, base_names)
                # XXX proper name for this attribute?
                #     or may be, store it in external storage?
                cls._iktomi_langs = langs
                setattr(module, lang_name, cls)


class LangModelProxy(object):

    def __init__(self, module, langs, lang):
        self.module = module
        self.langs = langs
        self.lang = lang.lower()
        self.lang_upper = lang.title()

    @cached_property
    def main_lang(self):
        return self.langs[0]

    def _get_model_name(self, name):
        return name + self.lang_upper

    def __getattr__(self, name):
        lang_name = self._get_model_name(name)
        if hasattr(self.module, lang_name):
            return getattr(self.module, lang_name)
        return getattr(self.module, name)


class ModelsProxy(object):

    def __init__(self, models, factories):
        self.models = models
        self.i18n_model_names = [m[0] for m in factories.i18n_models]
        self.model_names = [m[0] for m in factories.models]

    def __getattr__(self, name):
        try:
            return getattr(self.models, name)
        except AttributeError:
            if hasattr(self.models, 'lang'):
                if name in self.i18n_model_names:
                    lang_name = self.models._get_model_name(name)
                    return PseudoModel(lang_name)
            if name in self.model_names:
                return PseudoModel(name)
        raise AttributeError("{} has not attribute {}".format(repr(self), name))


class PseudoModel(str):

    def __new__(cls, name, parent=None):
        qname = '.'.join([parent, name]) if parent else name
        return str.__new__(cls, qname)

    def __getattr__(self, name):
        return PseudoModel(name, self)

