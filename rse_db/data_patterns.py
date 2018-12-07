import importlib
from datetime import datetime
from sqlalchemy import Column, DateTime, func, Integer
from sqlalchemy.orm.exc import NoResultFound

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


    def model_to_str(x, charset='utf8', errors='strict'):
        if x is None or isinstance(x, str):
            return x

        if isinstance(x, bytes):
            return x.decode(charset, errors)

        return str(x)


def get_filter_by_arguments(args, keys, kwargs):
    filter_args = kwargs
    if len(args) > 0:
        if len(keys) != len(args):
            raise ValueError(
                "Missing the required arguments. Please provide the following {}".format([k.key for k in keys]))
        for i in range(len(keys)):
            filter_args[keys[i].key] = args[i]
    return filter_args


class RSEReadOnlyModel(object):

    def __setattr__(self, name, value):
        """
        Raise an exception if attempting to assign to an atribute of a "read-only" object
        Transient attributes need to be prefixed with "_t_"
        """
        if (name != "_sa_instance_state"
                and not name.startswith("_t_")):
            raise ValueError("Trying to assign to %s of a read-only object %s" % (name, self))
        super().__setattr__(name, value)

    @classmethod
    def get_by_pk(cls, *args):
        # assume the arguments are in order by definition order
        keys = list(cls.__mapper__.primary_key)
        filter_args = get_filter_by_arguments(args, keys, {})
        try:
            result = cls.query.filter_by(**filter_args).one()
        except NoResultFound as e:
            key_str = ', '.join(['{}={}'.format(k,v) for k, v in filter_args.items()])
            plural_message = '' if len(filter_args.keys()) == 1 else 's'
            raise NoResultFound("Could not locate {} by"
                                " primary key{} of {}".format(cls.__name__, plural_message, key_str))
        return result

    @classmethod
    def find_one(cls, *args, **kwargs):
        keys = list(cls.__mapper__.primary_key)
        filter_args = get_filter_by_arguments(args, keys, kwargs)
        return cls.query.filter_by(**filter_args).one()

    @classmethod
    def find_one_or_none(cls, *args, **kwargs):
        keys = list(cls.__mapper__.primary_key)
        filter_args = get_filter_by_arguments(args, keys, kwargs)
        return cls.query.filter_by(**filter_args).one_or_none()

    @classmethod
    def find_first(cls, *args, order=None, **kwargs, ):
        keys = list(cls.__mapper__.primary_key)
        filter_args = get_filter_by_arguments(args, keys, kwargs)
        query = cls.query.filter_by(**filter_args)
        if order:
            query = query.order_by(order)
        return query.first()

    @classmethod
    def find_all(cls, *args, **kwargs):
        return cls.query.filter_by(*args, **kwargs).all()


class RSEBasicReadWriteModel(RSEReadOnlyModel):
    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)

    @classmethod
    def save(cls, new_instance, commit=True, session=None):
        if session is None:
            session = cls.query.session
        if not isinstance(new_instance, cls):
            raise ValueError("You must provide an instance of {}, not {}".format(cls.__name__, type(new_instance)))
        session.add(new_instance)
        if commit:
            session.commit()
        return new_instance

    @classmethod
    def delete_by_pk(cls, *args, commit=False, session=None):
        if session is None:
            session = cls.query.session
        item = cls.get_by_pk(*args)
        if item:
            session.delete(item)

        if commit:
            session.commit()

