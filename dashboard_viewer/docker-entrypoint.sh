#!/bin/bash

set -ex

# TODO create two cases: production and development

#if [ ${DASHBOARD_VIEWER_ENV} = "production" ]; then
#	exec gunicorn dashboard_viewer.wsgi:application --bind 0.0.0.0:8000 --workers 5
#else
	python manage.py runserver 0.0.0.0:8000
#fi 
