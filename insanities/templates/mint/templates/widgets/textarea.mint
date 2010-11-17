@textarea.id({{ widget.id }}).name({{ widget.input_name }})
    #if readonly:
        @.readonly(readonly)
    #if widget.classname:
        @+class({{ widget.classname }})
    {{ value }}
