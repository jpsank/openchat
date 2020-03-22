from flask import escape
from app import app
import re


def is_valid_name(text):
    """ Checks if name is valid (only ASCII printable characters, no slashes) """
    return all(32 <= ord(ch) <= 126 and ch != '/' for ch in text)


def nl2br(text):
    return text.replace('\n', '<br>')


@app.template_filter()
def censor(text):
    bad_words = {
        'dick': 1,
        'fuck': 1,
        'cock': 1
    }
    for bad_word, i in bad_words.items():
        for m in re.finditer(bad_word, text, re.IGNORECASE):
            ch_idx = m.start()+i
            text = text[:ch_idx] + '*' + text[ch_idx+1:]
    return text


# @app.context_processor
# def utility_processor():
#     return dict(escape=escape)
