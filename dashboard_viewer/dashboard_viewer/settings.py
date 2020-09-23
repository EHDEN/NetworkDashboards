"""
Django settings for dashboard_viewer project.

Generated by 'django-admin startproject' using Django 2.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DASHBOARD_VIEWER_ENV", "development") == "development"

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    # django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd party apps
    'bootstrap4',
    'bootstrap_datepicker_plus',
    'constance',
    'markdownify',
    'martor',
    'rest_framework',
    'sass_processor',

    # our apps
    'tabsManager',
    'uploader',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dashboard_viewer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, "shared/templates")
        ]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dashboard_viewer.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DEFAULT_DB', 'cdm'),
        'HOST': os.environ.get('POSTGRES_DEFAULT_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_DEFAULT_PORT', '5432'),
        'USER': os.environ.get('POSTGRES_DEFAULT_USER', 'cdm'),
        'PASSWORD': os.environ.get('POSTGRES_DEFAULT_PASSWORD', 'cdm'),
    },
    'achilles': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_ACHILLES_DB', 'achilles'),
        'HOST': os.environ.get('POSTGRES_ACHILLES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_ACHILLES_PORT', '5432'),
        'USER': os.environ.get('POSTGRES_ACHILLES_USER', 'achilles'),
        'PASSWORD': os.environ.get('POSTGRES_ACHILLES_PASSWORD', 'achilles'),
    }
}

DATABASE_ROUTERS = ['dashboard_viewer.routers.AchillesRouter']


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "static")
SASS_PROCESSOR_ROOT = STATIC_ROOT
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "node_modules"),
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
)

# Media files (Uploaded images, ...)
MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Uploader app specific settings
ACHILLES_RESULTS_STORAGE_PATH = "achilles_results_files"

# Celery
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
#REDIS_CACHE_DB = os.environ.get('REDIS_CACHE_DB', 0)
REDIS_CELERY_DB = os.environ.get('REDIS_CELERY_DB', 1)
REDIS_CONSTANCE_DB = os.environ.get('REDIS_CONSTANCE_DB', 2)

CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"

# Constance
CONSTANCE_REDIS_CONNECTION = {
    'host': REDIS_HOST,
    'port': REDIS_PORT,
    'db': REDIS_CONSTANCE_DB,
}
CONSTANCE_DBS = ["default"]

CONSTANCE_ADDITIONAL_FIELDS = {
    "image": ["django.forms.ImageField", {"required": False}],
    "url": ["django.forms.URLField", {"required": False}],
    "markdown": ["django.forms.CharField", {"widget": "martor.widgets.AdminMartorWidget", "required": False}]
}

CONSTANCE_CONFIG = {
    "APP_LOGO_IMAGE": (
        "CDM-BI-icon.png",
        "Image file to use as app logo.",
        "image"
    ),
    "APP_LOGO_URL": (
        "",
        "Url to the image to usa as app logo."
        "This setting will be used over the APP_LOG_IMAGE",
        "url"
    ),
    "APP_TITLE": (
        "Network Dashboards",
        "Title to use for the several pages",
        str,
    ),
    "LANDING_PAGE_DESCRIPTION": (
        "# Description\n"
        "TODO",
        "Land page desc",
        "markdown"
    ),
    "LANDING_PAGE_RESUME_DASHBOARD_URL": (
        "",
        "URL for the resume dashbaord of the network",
        "url"
    ),
    "UPLOADER_EXPORT": (
        "The Achilles tool generates summary statistics of the database that can be visualised in the Network Dashboard"
        " in the EHDEN portal. Information about the tool can be found on the"
        " [OHDSI Github Page](https://github.com/OHDSI/Achilles). Once the Achilles tool has run against your database"
        " you need to export the achilles results table to a csv file.",
        "Text for the 'Export Achilles results' section on the uploader app",
        "markdown"
    ),
    "UPLOADER_UPLOAD": (
        "The next step is to upload the Achilles result file in the portal using the form below. To update an existing"
        " database, you can simply upload the file and the data will be replaced. This operation can take some time to"
        " finish.",
        "Text for the 'Upload Achilles results' section on the uploader app",
        "markdown"
    ),
    "UPLOADER_AUTO_UPDATE": (
        "Once the Achilles results have been uploaded, all the graphs in the Network Dashboard will show the most"
        " recent data.",
        "Text for the 'Auto update dashboard' section on the uploader app",
        "markdown"
    ),
    "TABS_LOGO_CONTAINER_CSS": (
        "padding: 5px 5px 5px 5px;\n"
        "height: 100px;\n"
        "margin-bottom: 10px;\n",
        "Css for the div container of the logo image",
        str
    ),
    "TABS_LOGO_IMG_CSS": (
        "background: #fff;\n"
        "object-fit: contain;\n"
        "width: 90px;\n"
        "height: 100%;\n"
        "border-radius: 5px;\n"
        "padding: 0 5px 0 5px;\n"
        "transition: width 400ms, height 400ms;\n"
        "position: relative;\n"
        "z-index: 5;\n",
        "Css for the img tag displaying the app logo",
        str
    )
}

from django.dispatch import receiver
from constance.signals import config_updated


@receiver(config_updated)
def constance_updated(sender, key, old_value, new_value, **kwargs):
    if key == "APP_LOGO_IMAGE" and old_value:
        try:
            os.remove(os.path.join(MEDIA_ROOT, old_value))
        except FileNotFoundError:
            pass


# Markdown editor (Martor)
MARTOR_ENABLE_CONFIGS = {
    'emoji': 'false',
    'imgur': 'false',
    'mention': 'false',
    'jquery': 'true',
    'living': 'false',      # to enable/disable live updates in preview
    'spellcheck': 'true',
    'hljs': 'true',         # to enable/disable hljs highlighting in preview
}
