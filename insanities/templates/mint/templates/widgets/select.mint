@select.id({{ widget.id }}).name({{ widget.input_name }})
    #if widget.classname:
        @+class( {{ widget.classname }})
    #if widget.multiple:
        @.multiple(multiple)
    #if readonly:
        @.readonly(readonly)
    #if widget.size:
        @.size(size)
    #for op in options:
        @option.value({{ op['value'] }})
            #if op['selected']:
                @.selected(selected)
            {{ op['title'] }}
