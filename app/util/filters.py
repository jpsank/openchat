from app import app
import re


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

