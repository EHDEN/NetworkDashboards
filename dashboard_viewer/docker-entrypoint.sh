#!/bin/bash

set -ex

python manage.py migrate
python manage.py migrate --database=achilles

python manage.py compilescss
python manage.py collectstatic --noinput --ignore="*.scss"

if [ "${DASHBOARD_VIEWER_ENV}" = "production" ]; then
    exec gunicorn dashboard_viewer.wsgi:application --bind 0.0.0.0:8000 --workers 5
else
    python manage.py runserver 0.0.0.0:8000
fi
