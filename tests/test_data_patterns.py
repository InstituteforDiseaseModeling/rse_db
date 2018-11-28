import unittest
import sqlalchemy as sa
from sqlalchemy.orm.exc import NoResultFound

from rse_db.data_patterns import RSEReadOnlyModel
from rse_db.extensions import get_query_base_model
from rse_db.utils import get_db


class TestDataPattern(unittest.TestCase):
    def test_read_only_model(self):
        # connect to db
        db = get_db(connection_string='sqlite:///:memory:')
        # for cli/non-flask apps, we use the get_query base model. This replicates some of
        # Flask sqlalchemy's behaviour and adds a query property to the add a declarative model to the base
        base = get_query_base_model()

        # define our test model
        class User(base, RSEReadOnlyModel):
            __tablename__ = 'users'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String)

        base.metadata.create_all(db)
        user = User.find_first(1)
        self.assertIsNone(user)

        with self.assertRaises(NoResultFound):
            user = User.find_one(1)