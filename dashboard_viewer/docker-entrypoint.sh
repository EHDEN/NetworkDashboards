#!/bin/bash

set -ex

python manage.py migrate
python manage.py migrate --database=achilles uploader
python manage.py migrate --database=achilles materialized_queries_manager

if [ "${DASHBOARD_VIEWER_ENV}" = "production" ]; then
    python manage.py compilescss
    python manage.py collectstatic --noinput --ignore="*.scss"
    celery -A dashboard_viewer worker --loglevel=info &
    exec gunicorn dashboard_viewer.wsgi:application --bind 0.0.0.0:8000 --workers 5
else
    celery -A dashboard_viewer worker --loglevel=info &
    python manage.py runserver 0.0.0.0:8000
fi
