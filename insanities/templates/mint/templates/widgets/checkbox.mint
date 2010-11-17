@input.id({{ widget.id }}).type(checkbox).name({{ widget.input_name }})
    #if value:
        @.checked(checked)
    #if readonly:
        @.readonly(readonly)
