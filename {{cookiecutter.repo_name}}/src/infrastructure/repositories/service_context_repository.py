from src.domain.models import ServiceContext
from src.infrastructure.databases import sqlalchemy_db as db

from .repository import Repository


class ServiceContextRepository(Repository):
    base_class = ServiceContext

    def get_first(self):
        return db.session.query(self.base_class).first()