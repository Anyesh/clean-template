from functools import wraps

import jwt
from flask import current_app, request

from src.domain import (
    COOKIE_ALGORITHM,
    SECRET_KEY,
    SESSION_COOKIE_NAME,
    NoDataProvidedApiException,
    OperationalException,
)
from src.domain.exceptions import ApiException


def setup_prefix_middleware(app, prefix):
    if not app.config["TESTING"]:
        app.wsgi_app = PrefixMiddleware(app, prefix=prefix)

    return app


class PrefixMiddleware(object):
    ROUTE_NOT_FOUND_MESSAGE = "This url does not belong to the app."

    def __init__(self, app, prefix=""):
        self.app = app
        self.wsgi_app = app.wsgi_app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ["PATH_INFO"].startswith(self.prefix):
            environ["PATH_INFO"] = environ["PATH_INFO"][len(self.prefix) :]
            environ["SCRIPT_NAME"] = self.prefix
            return self.wsgi_app(environ, start_response)
        else:
            start_response("404", [("Content-Type", "text/plain")])
            return [self.ROUTE_NOT_FOUND_MESSAGE.encode()]


def post_data_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        json_data = request.get_json()
        if json_data is None or json_data == {}:
            raise NoDataProvidedApiException()
        else:
            return f(json_data, *args, **kwargs)

    return wrapped


def auth_requred(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        token = request.cookies.get(current_app.config[SESSION_COOKIE_NAME])
        if not token:
            raise ApiException("Unauthorized", 401)
        if not hasattr(current_app, "redis"):
            raise OperationalException("Redis not initialized")

        if not current_app.redis.get(token):
            raise ApiException("Unauthorized", 401)

        request.user = jwt.decode(
            token, current_app.config[SECRET_KEY], algorithms=[COOKIE_ALGORITHM]
        )
        return f(*args, **kwargs)

    return wrapped
