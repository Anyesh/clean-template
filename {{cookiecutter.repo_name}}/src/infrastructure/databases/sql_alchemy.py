from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from src.domain import SQLALCHEMY_DATABASE_URI, OperationalException

class Base(DeclarativeBase):
    ...

sqlalchemy_db = SQLAlchemy(model_class=Base)


class SQLAlchemyAdapter:

    def __init__(self, app):

        if app.config[SQLALCHEMY_DATABASE_URI] is not None:
            sqlalchemy_db.init_app(app)
            app.db = sqlalchemy_db
        elif not app.config["TESTING"]:
            raise OperationalException("SQLALCHEMY_DATABASE_URI not set")


def setup_sqlalchemy(app, throw_exception_if_not_set=True):

    try:
        SQLAlchemyAdapter(app)
    except OperationalException as e:
        if throw_exception_if_not_set:
            raise e

    return app
