from src.infrastructure.models import ServiceContext

from .repository import Repository


class ServiceContextRepository(Repository):
    base_class = ServiceContext

    def get_first(self):
        return self.session.query(self.base_class).first()
