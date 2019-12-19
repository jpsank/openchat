from flask import escape
from app import app


@app.template_filter()
def nl2br(text):
    return text.replace('\n', '<br>')


# @app.context_processor
# def utility_processor():
#     return dict(escape=escape)
