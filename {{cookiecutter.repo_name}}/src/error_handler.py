import logging
from typing import Dict, List

import marshmallow.exceptions as marshmallow_exceptions
from flask import jsonify
from sqlalchemy.exc import NoResultFound
from werkzeug.exceptions import HTTPException

from src.infrastructure import ApiException, ClientException

logger = logging.getLogger(__name__)


def setup_error_handler(app):
    """
    Function that will register all the specified error handlers for the app
    """

    def create_error_response(error_message, status_code: int = 400):
        # Remove the default 404 not found message if it exists
        if not isinstance(error_message, Dict):
            error_message = error_message.replace("404 Not Found: ", "")

        response = jsonify({"error_message": error_message})
        response.status_code = status_code
        return response

    def format_marshmallow_validation_error(errors: Dict):
        errors_message = {}

        for key in errors:
            if isinstance(errors[key], Dict):
                errors_message[key] = format_marshmallow_validation_error(errors[key])

            if isinstance(errors[key], List):
                errors_message[key] = errors[key][0].lower()
        return errors_message

    def error_handler(error):
        logger.error("exception of type {} occurred".format(type(error)))
        logger.exception(error)
        # Rollback any database changes that might have happened
        app.db.session.rollback()

        if isinstance(error, HTTPException):
            return create_error_response(str(error), error.code)
        elif isinstance(error, ClientException):
            return create_error_response(
                "Currently a dependent service is not available, "
                "please try again later",
                503,
            )
        elif isinstance(error, ApiException):
            return create_error_response(error.error_message, error.status_code)
        elif isinstance(error, marshmallow_exceptions.ValidationError):
            error_message = format_marshmallow_validation_error(error.messages)
            return create_error_response(error_message)
        elif isinstance(error, NoResultFound):
            return create_error_response("The requested resource was not found", 404)
        else:
            # Internal error happened that was unknown
            return create_error_response("Something went wrong! It's either you or us. Please try again later", 500)

    app.errorhandler(Exception)(error_handler)
    return app
