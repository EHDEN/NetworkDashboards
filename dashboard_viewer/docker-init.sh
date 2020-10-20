#!/bin/bash

set -ex

wait-for-it "$POSTGRES_DEFAULT_HOST:$POSTGRES_DEFAULT_PORT"
wait-for-it "$POSTGRES_ACHILLES_HOST:$POSTGRES_ACHILLES_PORT"

# Apply django migrations
python manage.py migrate
python manage.py migrate --database=achilles

# Load initial data
python manage.py load_data --app tabsManager initial_data
python manage.py load_data --app uploader --database achilles country_initial_data

# Create an user for the admin app
python manage.py createsuperuser
