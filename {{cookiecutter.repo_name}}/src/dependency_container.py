from dependency_injector import containers, providers

from src.config import Config
from src.infrastructure import ServiceContextService
from src.infrastructure.databases.redis_db import RedisSession
from src.infrastructure.databases.sql_alchemy import DatabaseSession
from src.infrastructure.repositories.service_context_repository import (
    ServiceContextRepository,
)


def setup_dependency_container(app, modules=None, packages=None):
    container = DependencyContainer()
    app.container = container
    app.container.wire(modules=modules, packages=packages)
    return app


class DependencyContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    wiring_config = containers.WiringConfiguration()

    db_session = providers.Singleton(DatabaseSession, db_uri=Config.SQLALCHEMY_DATABASE_URI)
    redis_session = providers.Singleton(RedisSession, redis_uri=Config.REDIS_URL)

    sc_repository = providers.Factory(ServiceContextRepository, session=db_session.provided.session)
    service_context_service = providers.Factory(ServiceContextService, repository=sc_repository)
