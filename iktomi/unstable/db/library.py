import sys

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
        self.lang_models = []

    def get_constructor(self, func):
        return return_locals(func)

    def register(self, *base_names, **kwargs):
        lang = kwargs.pop('lang', False)
        assert not kwargs
        def decor(func):
            name = func.func_name
            constructor = self.get_constructor(func)
            if lang:
                self.lang_models.append((name, constructor, base_names))
            else:
                self.models.append((name, constructor, base_names))
            return constructor
        return decor

    def create_model(self, models, name, constructor, base_names):
        bases = tuple(getattr(models, x) for x in base_names)
        values = constructor(models)
        cls = type(name, bases, values)
        cls.__module__ = models.__name__
        return cls

    def create_all(self, models, langs=()):
        for name, constructor, base_names in self.models:
            if hasattr(models, name):
                pass
            cls = self.create_model(models, name, constructor, base_names)
            setattr(models, name, cls)

        for lang in langs:
            lang_models = LangModelProxy(models, lang)
            for name, constructor, base_names in self.lang_models:
                lang_name = lang_models._get_model_name(name)
                if hasattr(models, lang_name):
                    pass
                cls = self.create_model(lang_models, lang_name,
                                        constructor, base_names)
                setattr(models, lang_name, cls)


class LangModelProxy(object):

    def __init__(self, models, lang):
        self.models = models
        self.lang = lang.lower()
        self.lang_upper = lang.title()

    def _get_model_name(self, name):
        return name + self.lang_upper

    def __getattr__(self, name):
        lang_name = self._get_model_name(name)
        if hasattr(self.models, lang_name):
            return getattr(self.models, lang_name)
        return getattr(self.models, name)
