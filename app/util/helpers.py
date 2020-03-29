import re


def is_valid_name(text):
    """ Checks if name is valid (only ASCII printable characters, no slashes) """
    return all(32 <= ord(ch) <= 126 and ch != '/' for ch in text)


def is_hex_color(string):
    m = re.fullmatch(r"#(?:[0-9a-fA-F]{1,2}){3}", string)
    return m is not None


def nl2br(text):
    return text.replace('\n', '<br>')