import json

from marshmallow import validates, ValidationError


def is_json_array(field):
    @validates(field)
    def check_field(self, key, value):
        # If this fails, it will throw a Marshmallow validation error
        p = json.loads(value)
        if not isinstance(p, list):
            raise ValidationError({field.__name__: "{} must be a json array".format(field.__name__)})
        return value


def is_schema_match(cls, schema, field):
    sh = schema(strict=True)

    def check_field(self, key, value):
        # If this fails, it will throw a Marshmallow validation error
        p = sh.loads(value)
        return value

    setattr(cls, 'validate_{}'.format(field), validates(check_field))
    return cls


