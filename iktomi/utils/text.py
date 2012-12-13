def pare(text, size, etc='...'):
    '''Pare text to have maximum size and add etc to the end if it's
    changed'''
    size = int(size)
    text = text.strip()
    if len(text)>size:
        text = text[:size]
        half = size//2
        last = None
        import re
        whitespace = re.compile('\s+')
        for mo in whitespace.finditer(text[half:]):
            if mo is not None:
                last = mo
        if last is not None:
            text = text[:half+last.start()+1]
        return text+etc
    else:
        return text
