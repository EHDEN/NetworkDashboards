#!/bin/bash

set -ex

wait-for-it $POSTGRES_DEFAULT_HOST:$POSTGRES_DEFAULT_PORT
wait-for-it $POSTGRES_ACHILLES_HOST:$POSTGRES_ACHILLES_PORT

# Apply django migrations
python manage.py migrate
python manage.py migrate --database=achilles uploader
python manage.py populate_countries

# Create an user for the admin app
python manage.py createsuperuser
