@input.type(password).value({{ value }}).name({{ widget.input_name }})
    #if readonly:
        @.readonly(readonly)
