#!/bin/bash

set -ex

python manage.py migrate

if [ ${DASHBOARD_VIEWER_ENV} = "production" ]; then
    python manage.py collectstatic --noinput
    celery -A dashboard_viewer worker --loglevel=info &
    exec gunicorn dashboard_viewer.wsgi:application --bind 0.0.0.0:8000 --workers 5
else
    python manage.py sass -t compressed tabsManager/static/scss/ tabsManager/static/css --watch &
    celery -A dashboard_viewer worker --loglevel=info &
    python manage.py runserver 0.0.0.0:8000
fi
