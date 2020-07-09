
# based on https://github.com/apache/incubator-superset/blob/49d672eb34fc26ca061ee19cb7a66c68bea128cc/contrib/docker/superset_config.py

import os


def get_env_variable(var_name, default=None):
    """Get the environment variable or raise exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        else:
            error_msg = 'The environment variable {} was missing, abort...'\
                        .format(var_name)
            raise EnvironmentError(error_msg)


POSTGRES_USER = get_env_variable('POSTGRES_USER')
POSTGRES_PASSWORD = get_env_variable('POSTGRES_PASSWORD')
POSTGRES_HOST = get_env_variable('POSTGRES_HOST')
POSTGRES_PORT = get_env_variable('POSTGRES_PORT')
POSTGRES_DB = get_env_variable('POSTGRES_DB')

# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = 'postgresql://%s:%s@%s:%s/%s' % (POSTGRES_USER,
                                                           POSTGRES_PASSWORD,
                                                           POSTGRES_HOST,
                                                           POSTGRES_PORT,
                                                           POSTGRES_DB)

REDIS_HOST = get_env_variable('REDIS_HOST')
REDIS_PORT = get_env_variable('REDIS_PORT')

CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_DEFAULT_TIMEOUT': 24 * 60 * 60, # 1 day (in secs)
    'CACHE_KEY_PREFIX': 'superset_results',
    'CACHE_REDIS_URL': f'redis://{REDIS_HOST}:{REDIS_PORT}/0',
}

class CeleryConfig(object):
    BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
    CELERY_IMPORTS = ('superset.sql_lab', )
    CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/1'
    CELERY_ANNOTATIONS = {'tasks.add': {'rate_limit': '10/s'}}
    CELERY_TASK_PROTOCOL = 1


CELERY_CONFIG = CeleryConfig
