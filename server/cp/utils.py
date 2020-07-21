
import tempfile
import libxmp.utils


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


def parse_xmp(binary):
    with tempfile.NamedTemporaryFile('wb') as _f:
        _f.write(binary.read())
        _f.flush()
        return libxmp.utils.file_to_dict(_f.name)
