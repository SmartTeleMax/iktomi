#for f in field.fields:
    @div.class(inner-field)
        #if f.label:
            @div.class(label)
                {{ f.label }}
        {{ utils.markup(f.render()) }}
        @div.class(clear)
