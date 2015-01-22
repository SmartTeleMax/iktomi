from iktomi.forms.form_json import FieldSet, Field, FileField
from .files import FileFieldSet, convs, check_file_path
from iktomi.forms import widgets_json as widgets


class FileFieldSet(FieldSet, FileFieldSet):

    fields = [
            FileField('file',
                  conv=convs.SimpleFile()),
            Field('mode',
                  conv=convs.EnumChoice(choices=[('existing', ''),
                                                 ('transient', ''),
                                                 ('empty', '')],
                                        required=True),
                  widget=widgets.HiddenInput),
            Field('transient_name',
                  conv=convs.Char(check_file_path, required=False),
                  widget=widgets.HiddenInput),
            Field('original_name',
                  conv=convs.Char(check_file_path, required=False),
                  widget=widgets.HiddenInput),
        ]
