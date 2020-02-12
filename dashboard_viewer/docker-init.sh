#!/bin/bash

set -ex

# Apply django migrations
python manage.py migrate
python manage.py migrate --database=achilles uploader
python manage.py populate_countries

# Create an user for the admin app
python manage.py createsuperuser
