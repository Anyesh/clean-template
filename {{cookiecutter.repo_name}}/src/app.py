import logging

from flask import jsonify, request

from src import api
from src.config import Config
from src.create_app import create_app

logger = logging.getLogger(__name__)
app = create_app(Config, dependency_container_packages=[api])


@app.before_request
def check_for_maintenance():
    if "maintenance" not in request.path and "status" not in request.path:
        service_context_service = app.container.service_context_service()
        status = service_context_service.get_service_context()

        if status.maintenance:
            return (
                jsonify({"message": "Service is currently enduring maintenance"}),
                503,
            )


@app.teardown_appcontext
def teardown_db(exception=None):
    if app.db is not None:
        if exception is None:
            app.db.session.commit()
        else:
            app.db.session.rollback()
        app.db.session.close()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="{{cookiecutter.port}}")
