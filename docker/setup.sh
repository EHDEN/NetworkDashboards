#!/bin/bash

echo "Setting up superset repo"
git clone https://github.com/apache/incubator-superset ../superset

cp ../superset/contrib/docker/superset_config.py ../superset

echo "Setting up the database for the superset app"
docker-compose run --rm -e FLASK_APP=superset superset flask fab create-db
docker-compose run --rm superset ./docker-init.sh

echo "Setting up the database for the dashboard viewer app"
docker-compose run --rm dashboard_viewer ./docker-init.sh
