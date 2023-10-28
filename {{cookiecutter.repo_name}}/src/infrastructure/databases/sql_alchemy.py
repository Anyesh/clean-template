from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from sqlalchemy import event
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool
from src.domain import SQLALCHEMY_DATABASE_URI, OperationalException
import os

class Base(MappedAsDataclass, DeclarativeBase):
    ...


class SQLAlchemyAdapter:
    def __init__(self, app):
        if app.config[SQLALCHEMY_DATABASE_URI] is not None:
            app.db = DatabaseSession(app, app.config[SQLALCHEMY_DATABASE_URI])
        elif not app.config["TESTING"]:
            raise OperationalException("SQLALCHEMY_DATABASE_URI not set")


def setup_sqlalchemy(app, throw_exception_if_not_set=True):
    try:
        SQLAlchemyAdapter(app)
    except OperationalException as e:
        if throw_exception_if_not_set:
            raise e

    return app




class DatabaseSession:
    def __init__(self, app=None, db_uri=None):
        self.app = app
        self.db_uri = db_uri
        self.session = None
        self.engine = None
        self.metadata = Base.metadata

        if app is not None and db_uri is not None:
            self.init_app(app, db_uri)

    def init_app(self, app, db_uri):
        app.config.setdefault('SQLALCHEMY_DATABASE_URI', db_uri)
        app.teardown_appcontext(self.teardown)

        engine = create_engine(db_uri, poolclass=StaticPool)  # connect_args={'check_same_thread': False} for sqlite 
        self.session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
        self.engine = engine

        @event.listens_for(engine, "connect")
        def connect(dbapi_connection, connection_record):
            connection_record.info['pid'] = os.getpid()

    def teardown(self, exception=None):
        if hasattr(self, 'session'):
            self.session.remove()

    def get_session(self):
        return self.session

    def create_all(self):
        self.metadata.create_all(self.engine)
    
    def drop_all(self):
        self.metadata.drop_all(self.engine)
