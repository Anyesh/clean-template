import os
from contextlib import contextmanager
from datetime import datetime

from flask import request
from sqlalchemy import DateTime, Engine, Integer, create_engine, event
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    Session,
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
            DatabaseSession(app, app.config[SQLALCHEMY_DATABASE_URI])
        elif not app.config["TESTING"]:
            raise OperationalException("SQLALCHEMY_DATABASE_URI not set")


def setup_sqlalchemy(app, throw_exception_if_not_set=True):
    try:
        SQLAlchemyAdapter(app)
    except OperationalException as e:
        if throw_exception_if_not_set:
            raise e

    return app


class Borg:
    _shared_state: dict[str, str] = {}

    def __init__(self) -> None:
        self.__dict__ = self._shared_state


class DatabaseSession(Borg):
    def __init__(self, app=None, db_uri=None):
        super().__init__()
        self.app = app
        self.db_uri = db_uri
        self.metadata = Base.metadata
        self.engine = self.create_engine(db_uri)
        self.session = self.create_session()
        self.base = None

        if app is not None and db_uri is not None:
            self.init_app(app, db_uri)

    @property
    def mapped_base(self):
        # Usage: current_app.db.mapped_base.classes.user(tablename)
        if self.base is None:
            self.metadata.reflect(bind=self.engine)
            self.base = automap_base(metadata=self.metadata)
            self.base.prepare()
        return self.base

    @contextmanager
    def session_context(self):
        session = self.session()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_session(self) -> scoped_session[Session]:
        if hasattr(self, "session"):
            return self.session

        return scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        )

    def create_engine(self, db_uri) -> Engine:
        if hasattr(self, "engine"):
            return self.engine

        engine = create_engine(
            db_uri, poolclass=StaticPool
        )  # connect_args={'check_same_thread': False} for sqlite
        return engine

    def init_app(self, app, db_uri):
        self.app = app
        app.config.setdefault("SQLALCHEMY_DATABASE_URI", db_uri)
        app.teardown_appcontext(self.teardown)

        app.db = self

        @event.listens_for(self.engine, "connect")
        def connect(dbapi_connection, connection_record):
            connection_record.info["pid"] = os.getpid()

        @event.listens_for(self.session, "before_flush")
        def before_flush(session, flush_context, instances):
            user_id = None  # Anon user
            for obj in session.new:
                if isinstance(obj, Mixin):
                    if request and hasattr(request, "user"):
                        user_id = request.user.get("id")
                    obj.created_by = user_id
                    obj.updated_by = user_id
                    obj.created_at = datetime.utcnow()
                    obj.updated_at = datetime.utcnow()
            for obj in session.dirty:
                if isinstance(obj, Mixin):
                    if request and hasattr(request, "user"):
                        user_id = request.user.get("id")
                    obj.updated_by = user_id
                    obj.updated_at = datetime.utcnow()

        @event.listens_for(self.engine, 'before_execute', retval=True)
        def intercept(conn, clauseelement, multiparams, params):
            from sqlalchemy.sql.selectable import Select

            # check if it's select statement
            if isinstance(clauseelement, Select):
                # 'froms' represents list of tables that statement is querying
                table = clauseelement.froms[0]

                # adding filter in clause
                if hasattr(table.c, 'is_deleted'):
                    clauseelement = clauseelement.where(table.c.is_deleted == False)


            return clauseelement, multiparams, params

        return app

    def teardown(self, exception=None):
        if hasattr(self, "session"):
            self.session.remove()

    def get_session(self):
        return self.session

    def create_all(self):
        self.metadata.create_all(self.engine)

    def drop_all(self):
        self.metadata.drop_all(self.engine)
