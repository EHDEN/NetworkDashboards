#!/bin/bash

set -ex

wait-for-it "$POSTGRES_DEFAULT_HOST:$POSTGRES_DEFAULT_PORT"
wait-for-it "$POSTGRES_ACHILLES_HOST:$POSTGRES_ACHILLES_PORT"

# Apply django migrations
python manage.py migrate
python manage.py migrate --database=achilles

# Load initial data
if [ $SUPERSET_URL == "" ] ; then
    1>&2 echo "Environment variable SUPERSET_URL not set"
    exit 1
fi

sed -i s/"{SUPERSET_URL}"/$SUPERSET_URL/ /app/dashboard_viewer/tabsManager/fixtures/initial_data.json
python manage.py loaddata --app tabsManager initial_data
python manage.py loaddata --app uploader --database achilles country_initial_data
python manage.py loaddata --app materialized_queries_manager --database achilles initial_data

# Create an user for the admin app
python manage.py createsuperuser
