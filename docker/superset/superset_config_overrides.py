import os


def get_env_variable(var_name, default=None):
    """Get the environment variable or raise exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default

        error_msg = "The environment variable {} was missing, abort...".format(
            var_name
        )
        raise EnvironmentError(error_msg)


PUBLIC_ROLE_LIKE_GAMMA = True


ENABLE_ROW_LEVEL_SECURITY = True


REDIS_HOST = get_env_variable("REDIS_HOST")
REDIS_PORT = get_env_variable("REDIS_PORT")
REDIS_CACHE_DB = get_env_variable("REDIS_CACHE_DB", 3)
REDIS_CELERY_DB = get_env_variable("REDIS_CELERY_DB", 4)

CACHE_CONFIG = {
    "CACHE_TYPE": "redis",
    "CACHE_DEFAULT_TIMEOUT": 24 * 60 * 60,  # 1 day (in secs)
    "CACHE_KEY_PREFIX": "superset_cache",
    "CACHE_REDIS_URL": f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CACHE_DB}",
}


class CeleryConfig(object):
    BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"
    CELERY_IMPORTS = ("superset.sql_lab",)
    CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"
    CELERY_ANNOTATIONS = {"tasks.add": {"rate_limit": "10/s"}}
    CELERY_TASK_PROTOCOL = 1


CELERY_CONFIG = CeleryConfig
