from redis import Redis

from src.infrastructure import REDIS_URL, OperationalException


def setup_redis(app, throw_exception_if_not_set=True):
    try:
        RedisAdapter(app)
    except OperationalException as e:
        if throw_exception_if_not_set:
            raise e

    return app


class RedisAdapter:
    def __init__(self, app):
        if app.config[REDIS_URL] is not None:
            RedisSession(app, app.config[REDIS_URL])
        elif not app.config["TESTING"]:
            raise OperationalException("REDIS_URL not set")


class RedisSession:
    def __init__(self, app=None, redis_uri=None):
        self.app = app
        self.redis_uri = redis_uri
        self.redis = Redis(decode_responses=True).from_url(redis_uri)

        if app is not None and redis_uri is not None:
            self.init_app(app, redis_uri)

    def init_app(self, app, redis_uri):
        self.app = app
        self.redis_uri = redis_uri

        app.redis = self.redis

        return app
