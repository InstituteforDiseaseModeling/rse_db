import os
from logging import getLogger
from typing import Callable
from flask.cli import AppGroup
from sqlalchemy.sql import ClauseElement

from rse_api.decorators import singleton_function
from sqlalchemy import create_engine, event
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
import importlib


HAS_FLASK_SQLALCHEMY = importlib.find_loader('flask_sqlalchemy') is not None
HAS_FLASK_MARSHMALLOW = importlib.find_loader('flask_marshmallow') is not None



def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance


@singleton_function
def get_declarative_base(**kwargs):
    """
    Default function for getting the declarative base class. There are cases you may want to do more to the class
    in which case you want to define another function in lieu of this one
    :return:
    """
    return declarative_base(**kwargs)


@singleton_function
def get_flask_marshmallow(app, db, declarative_base_func: Callable=get_declarative_base):
    """
    Gets the FlaskMarshmallow object. This is needed with Flask_Sqlalchmey to properly setup bindings

    :param app: App to add flask_marshmallow to
    :param db: db object to bind query property to per session
    :type db: SQLAlchemy
    :param declarative_base_func:
    :return: flask_marshmallow object
    :rtype: flask_marshmallow.Marshmallow
    """
    from flask_marshmallow import Marshmallow
    MA = Marshmallow(app)
    Base = declarative_base_func()
    Base.query = db.session.query_property()
    return MA, Base


def get_cli_commands(app, declarative_base_func: Callable=get_declarative_base):
    """
    Adds CLI commands for creating db, listing tables defined, and dropping tables

    :param app: App to add CLI commands to
    :param declarative_base_func: The function that fetch the declarative_base object
    :return: None
    """
    # Get flask db should have been called before this with any setup needed
    db_cli = AppGroup('db', help="Commands related to database")
    base = declarative_base_func()

    @db_cli.command('init', help="Creates database tables based off of loaded database models. If the table already "
                                 "exists, it will be skipped")
    def create_db():
        base.metadata.create_all(bind=get_engine(get_db()))

    @db_cli.command('drop_all', help="Drops all known tables in the schema")
    def drop_all():
        answer = ''
        while answer.lower() not in ['yes', 'y', 'no', 'n']:
            answer = input("Are you sure you want to delete all tables? [y/n]")

        if answer.lower() in ['yes', 'y']:
            base.metadata.drop_all(bind=get_engine(get_db()))

    @db_cli.command('list_tables', help="List all the tables available")
    def list_tables():
        for table in base.metadata.sorted_tables:
            print(table.name)

    app.cli.add_command(db_cli)


def get_engine(db) -> Engine:
    """
    Returns engine object from DB connection. This object could be a sqlalchemy.engine.Engine in which case we just
    return, otherwise, it could be a SQLAlchemy object, in which case we return the .engine attribute of the db
    :param db:
    :type db: Union[flask_sqlalchemy.SQLAlchemy,sqlalchemy.engine.Engine]
    :return: Engine object
    """
    engine = db
    if HAS_FLASK_SQLALCHEMY:
        from flask_sqlalchemy import SQLAlchemy
        if isinstance(engine, SQLAlchemy):
            engine = db.engine
    return engine


@singleton_function
def get_db(flask_app=None, get_models_func: Callable = None, declarative_base_func: Callable=get_declarative_base,
           connection_string: str=None, add_cli_commands=True):
    """
    Returns a DB object for flask. The function first attempts to load flask_sqlalchemy. If that is present,
    it will

    :param flask_app: Pass a flask application to the app if desired. Otherwise, get_application from rse_api will be called
    :param get_models_func: Function to call after loading the DB connection to load all the model files
    :param declarative_base_func: Function to call when loading the DB the first time to get a declartive base object.
    This function ideally should function as a singleton
    :param connection_string: Any SQLAlchemy connection string. See https://docs.sqlalchemy.org/en/latest/core/engines.html
    :return: Either a SQLAlchemy or Engine object representing a connection to the db
    :rtype: Union[flask_sqlalchemy.SQLAlchemy,sqlalchemy.engine.Engine]
    """

    # First check to see if we have SQLAlchemy
    if flask_app is not None and HAS_FLASK_SQLALCHEMY:
        from flask_sqlalchemy import SQLAlchemy
        db = SQLAlchemy(flask_app)
    else: # Otherwise fallback to create_engine
        if connection_string is None:
            raise ValueError("Connection string must be populated when you are not using flask_sqlalchemy.")
        db = create_engine(connection_string)

    # If the user has flask_marshmallow installed, lets use that. We define our declarative base there if specified
    if flask_app is not None and HAS_FLASK_SQLALCHEMY and HAS_FLASK_MARSHMALLOW:
        ma, base = get_flask_marshmallow(flask_app, db, declarative_base_func=declarative_base_func)

    # Otherwise see if we have a declarative_base_func defined
    elif declarative_base_func:
        base = declarative_base_func(bind=db)
        db.declartive_base = base

    # If a models function was specified, load all the models now
    if get_models_func:
        models = get_models_func()

    if declarative_base_func is not None and os.environ.get('FLASK_ENV', 'production') in ['development', 'testing'] \
                and os.environ.get('DEV_DB_CREATE', 'True').lower() in flask_app.config.get('TRUE_OPTIONS', ['true']):
        base.metadata.create_all(bind=get_engine(db))

    # Add our DB CLI commands
    if flask_app is not None and add_cli_commands:
        get_cli_commands(flask_app)
    return db


def setup_schema(Base, session):
    """
    Setups Marshmallow schema for any SqlAlchmey objects. This will have the absolutely minimal definitions and shold
    be use for initial development but most likely should not be used for final development


    :param Base: Base object(Delcarative base)
    :param session: Session of DB
    :return: Setup schema function that should be a called by 'after_configured' events
    :rtype: Callable
    """
    from marshmallow_sqlalchemy import ModelConversionError, ModelSchema
    def setup_schema(Base, session):
        # Create a function which incorporates the Base and session information
        def setup_schema_fn():
            for class_ in Base._decl_class_registry.values():
                if hasattr(class_, '__tablename__'):
                    if class_.__name__.endswith('Schema'):
                        raise ModelConversionError(
                            "For safety, setup_schema can not be used when a"
                            "Model class ends with 'Schema'"
                        )

                    class Meta(object):
                        model = class_
                        sqla_session = session

                    schema_class_name = '%sSchema' % class_.__name__

                    schema_class = type(
                        schema_class_name,
                        (ModelSchema,),
                        {'Meta': Meta}
                    )

                    setattr(class_, '__marshmallow__', schema_class)

        return setup_schema_fn

    # Create a function which incorporates the Base and session information
    def setup_schema_fn():
        for class_ in Base._decl_class_registry.values():
            if hasattr(class_, '__tablename__'):
                if class_.__name__.endswith('Schema'):
                    raise ModelConversionError(
                        "For safety, setup_schema can not be used when a"
                        "Model class ends with 'Schema'"
                    )

                class Meta(object):
                    model = class_
                    sqla_session = session

                schema_class_name = '%sSchema' % class_.__name__

                schema_class = type(
                    schema_class_name,
                    (ModelSchema,),
                    {'Meta': Meta}
                )

                setattr(class_, '__marshmallow__', schema_class)

    return setup_schema_fn


def auto_generate_schemas(Base, session):
    event.listen(mapper, 'after_configured', setup_schema(Base, session))