#!/bin/bash

set -e

wait-for-it "$POSTGRES_DEFAULT_HOST:$POSTGRES_DEFAULT_PORT"
wait-for-it "$POSTGRES_ACHILLES_HOST:$POSTGRES_ACHILLES_PORT"

# Apply django migrations
echo "Applying migrations"
python manage.py migrate
python manage.py migrate --database=achilles

# Load countries data
echo "Loading initial data"
countries_count=$(echo "
from uploader.models import Country
print(Country.objects.count())
" | python manage.py shell)
if [[ $countries_count -gt 0 ]] ; then
    echo "Countries tables has data. Skipping initial data load"
else
    python manage.py loaddata --database=achilles countries
fi


# Create an user for the admin app
echo "Creating super user"
python manage.py createsuperuser
