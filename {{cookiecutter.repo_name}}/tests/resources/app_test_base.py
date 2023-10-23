from pathlib import Path

from flask_testing import TestCase
from src import api
from src.config import Config
from src.create_app import create_app
from src.domain import SQLALCHEMY_DATABASE_URI
# from src.infrastructure import setup_sqlalchemy
from src.infrastructure import sqlalchemy_db as db
from testcontainers.postgres import PostgresContainer

PROJECT_ROOT = str(Path(__file__).parent.parent.parent)


class SqliteDBContainer:
    def get_connection_url(self):
        return "sqlite:///:memory:"

    def stop(self):
        pass


class AppTestBase(TestCase):
    def setup_database(self):
        self.db_container = self._setup_postgres()
        self.app.config[
            SQLALCHEMY_DATABASE_URI
        ] = self.db_container.get_connection_url()
        # setup_sqlalchemy(self.app)
        self.clear_database()

    def _setup_postgres(self):
        try:
            return PostgresContainer(image="postgres:14").start()
        except Exception as e:
            return SqliteDBContainer()

    def teardown_database(self):
        if self.db_container is not None:
            db.session.commit()
            db.session.close()
            self.db_container.stop()

    def clear_database(self):
        if self.db_container is not None:
            db.drop_all()
            db.create_all()

    def create_app(self):
        config = Config()
        config["TESTING"] = True
        return create_app(config, dependency_container_packages=[api])

    def tearDown(self) -> None:
        self.teardown_database()
