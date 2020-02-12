#!/bin/bash

echo "Setting up superset repo"
docker_dir=$(pwd)
git clone https://github.com/apache/incubator-superset ../superset
cd ../superset && git checkout tags/0.35.1 -b tag0.35.1
cd $docker_dir
cp ../superset/contrib/docker/superset_config.py ../superset

echo "Setting up the database for the superset app"
#This command was necessary one time for a specific installation, but usually the system can be installed without it
#docker-compose run --rm -e FLASK_APP=superset superset flask fab create-db
docker-compose run --rm superset ./docker-init.sh

echo "Setting up the database for the dashboard viewer app"
docker-compose run --rm dashboard_viewer ./docker-init.sh
