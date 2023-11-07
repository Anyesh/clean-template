import logging

from dependency_injector.wiring import Provide, inject
from flask import Blueprint, jsonify
from src.api.schemas import ServiceContextSchema
from src.dependency_container import DependencyContainer
from totoro.common.responses import create_response

logger = logging.getLogger(__name__)
blueprint = Blueprint("service_context", __name__)


@blueprint.route("/service-context", methods=["GET"])
@inject
def get_service_status(
    service_context_service=Provide[DependencyContainer.service_context_service],
):
    status = service_context_service.get_service_context()
    return create_response(status, ServiceContextSchema)


@blueprint.route("/ping", methods=["GET"])
def ping_service():
    return jsonify({"message": "pong from {{cookiecutter.repo_name}}"})
