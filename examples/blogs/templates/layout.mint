{{ utils.HTML_STRICT }}
@html
    @head
        @title {{ 'Example blog'}}

        #def css():
            @style
        #css()

        #def js()
            @script.type(text/javascript)
        #js()

    @body
        @form.action({{ VALS.url_for('change_language') }}).method(POST)
            @input.type(submit).name(language).value({{ language=='en' and 'ru' or 'en' }})
        #content()
