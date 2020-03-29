from wtforms.validators import ValidationError, Length

from app.util.helpers import is_valid_name, is_hex_color


class Unique:
    def __init__(self, query_func, allowed=(), message=u'This element already exists.'):
        self.query_func = query_func
        self.allowed = allowed
        self.message = message

    def __call__(self, form, field):
        if field.data not in self.allowed and self.query_func(field.data) is not None:
            raise ValidationError(self.message)


class ValidName:
    def __init__(self, message=u'Name must contain only ASCII printable characters'):
        self.message = message

    def __call__(self, form, field):
        if not is_valid_name(field.data):
            raise ValidationError(self.message)


class ValidLength(Length):
    def __init__(self, column, message=None):
        super().__init__(min=0, max=column.type.length, message=message)


class HexColor:
    def __init__(self, message=u'Must be a hex color code'):
        self.message = message

    def __call__(self, form, field):
        if not is_hex_color(field.data):
            raise ValidationError(self.message)
