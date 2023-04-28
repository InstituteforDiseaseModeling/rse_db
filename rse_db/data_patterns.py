import importlib
from datetime import datetime

from sqlalchemy import Column, DateTime, func, Integer
from sqlalchemy.orm.exc import NoResultFound

HAS_MARSHMALLOW = importlib.find_loader("marshmallow") is not None


class IdMixin(object):
    """
    Simple ID column for SqlAlchemy
    """

    id = Column(Integer, autoincrement=True, primary_key=True)


class CreatedAtMixin(object):
    """
    DB Model with a created at column by that is populated with the current time by default
    """

    created_at = Column(DateTime, server_default=func.now())


class CreatedAndUpdatedAtMixin(object):
    """
    DB Model with a created at and updated at columns. Created at is set to the current time when object is inserted
    into db and updated at is set to the current time when an object is saved/inserted
    """

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now())


# If we have marshmallow, declare schema mixins as well
if HAS_MARSHMALLOW:
    from marshmallow import fields, validate, post_load, ValidationError

    class IdSchemaMixin(object):
        """
        Marshmallow Schema mixing to match IdMixin DB Model

        See Also:
            - :meth:`rse_db.data_patterns.IdMixin`
        """

        id = fields.Integer(required=True, validate=validate.Range(min=0))

    class CreatedAtSchemaMixin(object):
        """
        Marshmallow Schema mixing to match CreatedAtMixin DB Model

        See Also:
            - :meth:`rse_db.data_patterns.CreatedAtMixin`
        """

        created_at = fields.DateTime(default=datetime.now(), allow_none=False)

    class CreatedAndUpdatedAtSchemaMixin(object):
        """
        Marshmallow Schema mixing to match CreatedAtMixin DB Model

        See Also:
            - :meth:`rse_db.data_patterns.CreatedAtMixin`
        """

        created_at = fields.DateTime(format="iso", missing=datetime.now().isoformat(), allow_none=False)
        updated_at = fields.DateTime(format="iso", missing=datetime.now().isoformat(), allow_none=False)

        @post_load
        def ensure_updated_is_greater_than_created(self, item):
            """
            Validation method to ensure that updated at is not less than created at
            Args:
                item: Item we are verifying

            Returns:

            """
            if "updated_at" in item and "created_at" in item:
                updated_at = datetime.fromisoformat(item["updated_at"]) if isinstance(item["updated_at"], str) else item["updated_at"]
                created_at = datetime.fromisoformat(item["created_at"]) if isinstance(item["updated_at"], str) else item["created_at"]
                if updated_at < created_at:
                    error_message = "Updated at cannot be greater than created at"
                    raise ValidationError({"created_at": error_message, "updated_at": error_message})
            return item

    def model_to_str(x, charset="utf8", errors="strict"):
        if x is None or isinstance(x, str):
            return x

        if isinstance(x, bytes):
            return x.decode(charset, errors)

        return str(x)


def get_filter_by_arguments(args, keys, kwargs):
    """
    Attempts to validate and build a set of generic filter arguments for the RSEReadOnlyModel models

    Args:
        args: Args to map to keys
        keys: Keys to map args too
        kwargs:  Set of additional arguments passed to filter

    Returns:
        Dict containing a mapping of keyword arguments to be used when calling ".filter" on an SqlAlchmey Model
    """
    filter_args = kwargs
    if len(args) > 0:
        if len(keys) != len(args):
            raise ValueError("Missing the required arguments. Please provide the following {}".format([k.key for k in keys]))
        for i in range(len(keys)):
            filter_args[keys[i].key] = args[i]
    return filter_args


class RSEReadOnlyModel(object):
    def __setattr__(self, name, value):
        """
        Raise an exception if attempting to assign to an atribute of a "read-only" object
        Transient attributes need to be prefixed with "_t_"

        Args:
            name: Attribute name
            value: Value to set

        Raises:
            ValueError when attemping to set any property since the item is read-only
        """
        if name != "_sa_instance_state" and not name.startswith("_t_"):
            raise ValueError("Trying to assign to %s of a read-only object %s" % (name, self))
        super().__setattr__(name, value)

    @classmethod
    def get_by_pk(cls, *args):
        """
        Lookup model by Primary Key(s)

        Args:
            *args: A list of keys. This should match the definition order of the specified Ids within the model

        Raises:
            NoResultFound if a record with specified id(s) cannot be found
        Returns:
            Instance of the model if Found
        """
        # assume the arguments are in order by definition order
        keys = list(cls.__mapper__.primary_key)
        filter_args = get_filter_by_arguments(args, keys, {})
        try:
            result = cls.query.filter_by(**filter_args).one()
        except NoResultFound:
            key_str = ", ".join(["{}={}".format(k, v) for k, v in filter_args.items()])
            plural_message = "" if len(filter_args.keys()) == 1 else "s"
            raise NoResultFound("Could not locate {} by" " primary key{} of {}".format(cls.__name__, plural_message, key_str))
        return result

    @classmethod
    def find_one(cls, *args, **kwargs):
        """
        Find One specific item by primary keys and additional set of filter options to be passed to filter_by

        Args:
            *args: List of id(s)
            **kwargs: List of additional items to pass to filter_by

        Returns:
            The specific model if Found

        See Also:
            - https://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.filter_by
        """
        keys = list(cls.__mapper__.primary_key)
        filter_args = get_filter_by_arguments(args, keys, kwargs)
        return cls.query.filter_by(**filter_args).one()

    @classmethod
    def find_one_or_none(cls, *args, **kwargs):
        """
        Find One specific item by primary keys and additional set of filter options to be passed to filter_by.
        If an item cannot be found, the value None is returned

        Args:
            *args: List of id(s)
            **kwargs: List of additional items to pass to filter_by

        Returns:
            Model of object or None

        See Also:
            - https://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.filter_by

        """
        keys = list(cls.__mapper__.primary_key)
        filter_args = get_filter_by_arguments(args, keys, kwargs)
        return cls.query.filter_by(**filter_args).one_or_none()

    @classmethod
    def find_first(cls, *args, order=None, **kwargs):
        """
        Find the first item that matches a query

        Args:
            *args: List of id(s)
            order: Optional order to sort the results. See order_by in SqlAlchemy docs
            **kwargs: List of additional items to pass to filter_by

        Returns:
            - https://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.filter_by
            - https://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.order_by
        """
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

    def commit(self):
        """
        Convenience method to allow saving an object directly

        Returns:
            Self - This is useful in Requests where we want to return model for Serialization after saving
        """
        s = type(self).query.session
        s.add(self)
        s.commit()
        return self

    @classmethod
    def save(cls, new_instance: "RSEBasicReadWriteModel", commit: bool = True, session=None):
        """
        Save a new copy of an item.

        Args:
            new_instance: an instance of the item to be saved
            commit: Flag to autocommit after saving. The default is true. For large sets of insertions, you will
                want to reuse the session and only commit the transaction after all items have been "saved"
            session: Optional DB session to use

        Returns:
            Copy of new instance that was Saved
        """
        if session is None:
            session = cls.query.session
        if not isinstance(new_instance, cls):
            raise ValueError("You must provide an instance of {}, not {}".format(cls.__name__, type(new_instance)))
        session.add(new_instance)
        if commit:
            session.commit()
        return new_instance

    @classmethod
    def delete_by_pk(cls, *args, commit: bool = False, session=None):
        """
        Delete an item by a primary key(s)
        Args:
            *args: List of id(s) in the definition order of their source model
            commit: Flag to autocommit after saving. The default is true. For transactions you can resuse the same
                session and set this to False. Then a session commit after all deletions have been executed will
                be the most efficient
            session: Optional db session object

        Returns:
            None
        """
        if session is None:
            session = cls.query.session
        item = cls.get_by_pk(*args)
        if item:
            session.delete(item)

        if commit:
            session.commit()
