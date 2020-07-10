

def format_maxlength(text, length):
    if not text:
        return text
    output = ''
    for word in text.split(' '):
        space = ' ' if len(output) else ''
        if len(output) + len(word) + len(space) > length:
            break
        output = '{}{}{}'.format(output, space, word)
    return output
