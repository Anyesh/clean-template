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
            app.redis = Redis.from_url(app.config[REDIS_URL])
        elif not app.config["TESTING"]:
            raise OperationalException("REDIS_URL not set")
