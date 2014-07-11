from iktomi.utils import cached_property
from .base import Cli

class LazyCli(Cli):
    '''
    Wrapper for creating lazy command digests.

    Sometimes it is not needed to import all of application parts to start
    a particular command. LazyCli allows you to define all imports in a 
    function called only on the command::

        @LazyCli
        def db_command():
            import admin
            from admin.environment import db_maker

            from models import initial
            from iktomi.cli import sqla
            return sqla.Sqla(db_maker, initial=initial.install)

        # ...

        def run(args=sys.argv):
            manage(dict(db=db_command, ), args)
    '''
    def __init__(self, func):
        self.get_digest = func

    @cached_property
    def digest(self):
        return self.get_digest()

    def description(self, *args, **kwargs):
        return self.digest.description(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.digest(*args, **kwargs)
