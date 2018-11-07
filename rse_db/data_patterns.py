import importlib
from datetime import datetime

from sqlalchemy import Column, DateTime, func, Integer

HAS_MARSHMALLOW = importlib.find_loader('marshmallow') is not None


class IdMixin(object):
    id = Column(Integer, autoincrement=True, primary_key=True)


class CreatedAtMixin(object):
    created_at = Column(DateTime, default=func.now())


class CreatedAndUpdatedAtMixin(object):
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# If we have marshmallow, declare schema mixins as well
if HAS_MARSHMALLOW:
    from marshmallow import fields, validate, post_load, ValidationError

    class IdSchemaMixin(object):
        id = fields.Integer(required=True, validate=validate.Range(min=0))


    class CreatedAtSchemaMixin(object):
        created_at = fields.DateTime(default=datetime.now(), allow_none=False)


    class CreatedAndUpdatedAtSchemaMixin(object):
        created_at = fields.DateTime(format='iso', missing=datetime.now().isoformat(), dallow_none=False)
        updated_at = fields.DateTime(format='iso', missing=datetime.now().isoformat(), allow_none=False)

        @post_load
        def ensure_updated_is_greater_than_created(self, item):
            if 'updated_at' in item and 'created_at' in item:
                updated_at = datetime.fromisoformat(item['updated_at']) if isinstance(item['updated_at'], str) else item['updated_at']
                created_at = datetime.fromisoformat(item['created_at']) if isinstance(item['updated_at'], str) else item['created_at']
                if updated_at < created_at:
                    error_message = "Updated at cannot be greater than created at"
                    raise ValidationError({
                        'created_at': error_message,
                        'updated_at': error_message
                    })


class CRUDModel(object):

    @classmethod
    def get_by_pk(cls, *args):
        #assume the arguments are in order by definition order
        filter_args = {}
        keys = list(cls.__mapper__.primary_key)
        if len(keys) != len(args):
            raise ValueError("Missing the required arguments. Please provide the following {}".format([k.key for k in keys]))
        for i in range(len(keys)):
            filter_args[keys[i].key] = args[i]
        return cls.query.filter_by(**filter_args).one()

    @classmethod
    def find_all(cls, *args, **kwargs):
        return cls.query.filter_by(**kwargs)

    @classmethod
    def create(cls, new_instance, commit=True, session=None):
        if session is None:
            session = cls.query.session
        if not isinstance(new_instance, cls):
            raise ValueError("You must provide an instance of {}, not {}".format(cls.__name__, type(new_instance)))
        session.add(new_instance)
        if commit:
            session.commit()
        return session

    @classmethod
    def delete_by_pk(cls, *args, commit=False, session=None):
        if session is None:
            session = cls.query.session
        item = cls.get_by_pk(*args)
        if item:
            session.delete(item)

        if commit:
            session.commit()