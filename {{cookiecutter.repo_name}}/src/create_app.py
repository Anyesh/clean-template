from flask import Flask
from src.api import setup_blueprints
from src.cors import setup_cors
from src.dependency_container import setup_dependency_container
from src.domain import SERVICE_PREFIX
from src.error_handler import setup_error_handler
from src.infrastructure import setup_redis, setup_sqlalchemy
from src.logging import setup_logging
from src.management import setup_management
from totoro_common.middlewares import setup_prefix_middleware


def create_app(
    config,
    dependency_container_packages=None,
    dependency_container_modules=None,
):
    app = Flask(__name__.split(".")[0])
    app.db = None
    app = setup_logging(app)
    app.config.from_object(config)
    app = setup_cors(app)
    app.url_map.strict_slashes = False
    app = setup_prefix_middleware(app, prefix=app.config[SERVICE_PREFIX])
    app = setup_blueprints(app)
    app = setup_sqlalchemy(app)  # app.db will be available after this
    app = setup_redis(app)  # app.redis will be available after this
    app = setup_error_handler(app)
    app = setup_management(app)

    # Dependency injection container initialization should be done last
    app = setup_dependency_container(
        app,
        packages=dependency_container_packages,
        modules=dependency_container_modules,
    )
    return app
