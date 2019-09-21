#!/bin/bash

set -ex

# Apply django migrations
python manage.py migrate

# Create an user for the admin app
python manage.py createsuperuser
