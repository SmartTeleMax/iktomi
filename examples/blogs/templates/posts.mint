#base: layout.mint

#def css()
    @style
        ul.paginator li {list-style: none; display: inline;}
        ul.paginator li a.current-page {text-decoration: none; color: #900;}
        a {color: #000;}
        a.action {color: #900;}

#def content()

    @h3 {{ 'This is my small blog' }}

    #if not paginator.items
        @p {{ 'There is no posts yet' }}

    @ul
        #for post in paginator.items
            @li
                @a.href({{ VALS.url_for('mint-post', id=post.id) }}) {{ post.title }}
                #if VALS.user
                    @a.class(action).href({{ VALS.url_for('edit-post', id=post.id) }})
                        {{ 'edit' }}
                    @a.class(action).href({{ VALS.url_for('del-post', id=post.id) }})
                        {{ 'delete' }}

    #if paginator.pages_count > 1
        @ul.class(paginator)
            #for p, url in paginator.pages
                @li
                    @a.class({{ p==paginator.page and 'current-page' or '' }}).href({{ url }}) {{ p }}

    @div.clas(actoins)
        #if VALS.user:
            @a.href({{ VALS.url_for('add-post') }}) {{ 'add post' }}
            @a.href({{ VALS.url_for('logout') }}) {{ 'logout' }}
        #else:
            @a.href({{ VALS.url_for('login') }}) {{ 'login' }}
