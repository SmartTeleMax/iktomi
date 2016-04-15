import re


whitespace_re = re.compile('\s+')

def pare(text, size, etc='...'):
    '''Pare text to have maximum size and add etc to the end if it's
    changed'''
    size = int(size)
    text = text.strip()
    if len(text)>size:
        # strip the last word or not
        to_be_stripped = not whitespace_re.findall(text[size-1:size+2])

        text = text[:size]
        if to_be_stripped:
            half = size//2
            last = None
            for mo in whitespace_re.finditer(text[half:]):
                last = mo

            if last is not None:
                text = text[:half+last.start()+1]

        return text.rstrip() + etc
    else:
        return text
