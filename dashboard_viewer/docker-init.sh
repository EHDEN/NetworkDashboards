#!/bin/bash

set -ex

# Apply django migrations
python manage.py migrate
python manage.py migrate --database=achilles uploader

# Create an user for the admin app
python manage.py createsuperuser
