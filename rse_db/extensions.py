from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import UnmappedClassError
from rse_api import singleton_function
from sqlalchemy.orm import sessionmaker

@singleton_function
def get_session_maker():
    from rse_db.utils import get_db
    return sessionmaker(bind=get_db())


def get_session():
    return get_session_maker()()


class RSEBaseQuery(orm.Query):
    pass


class RSEQueryBaseModel(object):
    query = None


class RSEQueryProperty(object):
    def __init__(self, get_session_callback=get_session):
        self.get_session = get_session_callback

    def __get__(self, obj, type):
        try:
            mapper = orm.class_mapper(type)
            if mapper:
                return RSEBaseQuery(mapper, session=self.get_session())
        except UnmappedClassError:
            return None


@singleton_function
def get_query_base_model(get_session_callback=get_session):
    base = declarative_base(cls=RSEQueryBaseModel)
    base.query = RSEQueryProperty(get_session_callback)
    return base