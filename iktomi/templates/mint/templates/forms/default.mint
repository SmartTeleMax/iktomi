#for field in form.fields:
    @div.class(field)
        #if field.error:
            @p.class(error) {{ field.error }}
        #if field.label:
            @div.class(label) {{ field.label }}
        {{ utils.markup(field.render()) }}
        @div.class(clear)
