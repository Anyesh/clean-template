import os
from datetime import datetime

from flask import request
from sqlalchemy import DateTime, Integer, create_engine, event
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    scoped_session,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

from src.infrastructure import SQLALCHEMY_DATABASE_URI, OperationalException


class Base(MappedAsDataclass, DeclarativeBase):
    ...


class Mixin(MappedAsDataclass):
    created_by: Mapped[int] = mapped_column(Integer, init=False)
    updated_by: Mapped[int] = mapped_column(Integer, init=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, init=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, onupdate=datetime.utcnow, init=False
    )


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
        self.base = None
        self.metadata = Base.metadata

        if app is not None and db_uri is not None:
            self.init_app(app, db_uri)

    def create_engine(self, db_uri):
        engine = create_engine(
            db_uri, poolclass=StaticPool
        )  # connect_args={'check_same_thread': False} for sqlite
        self.metadata.reflect(bind=engine)
        self.session = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=engine)
        )
        self.engine = engine
        self.base = automap_base(metadata=self.metadata)
        self.base.prepare()
        return engine

    def init_app(self, app, db_uri):
        app.config.setdefault("SQLALCHEMY_DATABASE_URI", db_uri)
        app.teardown_appcontext(self.teardown)

        engine = self.create_engine(db_uri)

        @event.listens_for(engine, "connect")
        def connect(dbapi_connection, connection_record):
            connection_record.info["pid"] = os.getpid()

        @event.listens_for(self.session, "before_flush")
        def before_flush(session, flush_context, instances):
            user_id = 0  # Anon user
            for obj in session.new:
                if isinstance(obj, Mixin):
                    if hasattr(request, "user"):
                        user_id = request.user.get("id")
                    obj.created_by = user_id
                    obj.updated_by = user_id
                    obj.created_at = datetime.utcnow()
                    obj.updated_at = datetime.utcnow()
            for obj in session.dirty:
                if isinstance(obj, Mixin):
                    if hasattr(request, "user"):
                        user_id = request.user.get("id")
                    obj.updated_by = user_id
                    obj.updated_at = datetime.utcnow()

    def teardown(self, exception=None):
        if hasattr(self, "session"):
            self.session.remove()

    def get_session(self):
        return self.session

    def create_all(self):
        self.metadata.create_all(self.engine)

    def drop_all(self):
        self.metadata.drop_all(self.engine)
