#!/bin/bash

set -ex

# TODO create two cases: production and development
if [ ${DASHBOARD_VIEWER_ENV} = "production" ]; then
	python manage.py collectstatic --noinput
	exec gunicorn genericcdss.wsgi:application --bind 0.0.0.0:8000 --workers 5
else
	python manage.py runserver 0.0.0.0:8000
fi