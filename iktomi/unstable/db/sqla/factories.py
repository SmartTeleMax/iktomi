import sys
from iktomi.utils import cached_property

def return_locals(func):
    '''
        Wraps function, so it is executed and it's locals() are returned
    '''

    def wrap(*args, **kwargs):
        frames = []
        def tracer(frame, event, arg):
            sys.setprofile(oldprofile)
            frames.append(frame)

        oldprofile = sys.getprofile()
        # tracer is activated on next call, return or exception
        sys.setprofile(tracer)
        try:
            func(*args, **kwargs)
        finally:
            sys.setprofile(oldprofile)
        assert len(frames) == 1
        return frames.pop(0).f_locals
    return wrap


class ModelLibrary(object):

    def __init__(self):
        self.models = []
        self.i18n_models = []

    def get_constructor(self, func):
        return return_locals(func)

    def register(self, *base_names, **kwargs):
        lang = kwargs.pop('lang', False)
        assert not kwargs
        def decor(func):
            name = func.func_name
            constructor = self.get_constructor(func)
            if lang:
                self.i18n_models.append((name, constructor, base_names))
            else:
                self.models.append((name, constructor, base_names))
            return constructor
        return decor

    def create_model(self, module, name, constructor, base_names):
        bases = tuple(getattr(module, x) for x in base_names)
        values = constructor(module)
        cls = type(name, bases, values)
        cls.__module__ = module.__name__
        return cls

    def create_all(self, module, all_lang_models=()):
        for name, constructor, base_names in self.models:
            if hasattr(module, name):
                pass
            cls = self.create_model(module, name, constructor, base_names)
            setattr(module, name, cls)

        for lang_models in all_lang_models:
            for name, constructor, base_names in self.i18n_models:
                lang_name = lang_models._get_model_name(name)
                if hasattr(module, lang_name):
                    pass
                cls = self.create_model(lang_models, lang_name,
                                        constructor, base_names)
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
