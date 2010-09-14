#base: layout.mint

#def content()
    @a.href({{ VALS.url_for('mint-posts') }}) {{ 'back to posts page' }}
    @p.class(title) {{ post.title }}
    {{ post.body }}
