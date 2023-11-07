from src.infrastructure.models import ServiceContext
from src.infrastructure.repositories import ServiceContextRepository


class ServiceContextService:
    def __init__(self, repository: ServiceContextRepository | None = None):
        self.repository = repository or ServiceContextRepository()

    def update(self, data):
        service_context = self.repository.get_first()

        if service_context is None:
            service_context = ServiceContext()
            self.repository.save(service_context)

        self.repository.update(service_context.id, data)
        return service_context

    def get_service_context(self):
        status = self.repository.get_first()

        if status is None:
            enitity = ServiceContext()
            return self.repository.save(enitity)

        return status
