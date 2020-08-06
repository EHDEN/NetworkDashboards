#!/bin/bash

echo "Setting up superset repo"
#git clone https://github.com/apache/incubator-superset ../superset
#cd ../superset && git checkout tags/0.35.1 -b tag0.35.1 && cd ../docker

echo "Performing replacements related with URL suffix"
cd ./replace-files && sh replacements.sh && cd ..
cp ./replace-files/base.html ../superset/superset/templates/superset/base.html
cp ./replace-files/basic.html ../superset/superset/templates/superset/basic.html
cp ./replace-files/theme.html ../superset/superset/templates/superset/theme.html
cp ./replace-files/webpack.config.js ../superset/superset/assets/webpack.config.js
cp ./replace-files/Loading.jsx ../superset/superset/assets/src/components/Loading.jsx
cp ./replace-files/DisplayQueryButton.jsx ../superset/superset/assets/src/explore/components/DisplayQueryButton.jsx

cp ./superset_config.py ../superset

echo "Setting up the database for the superset app"
#docker-compose run --rm -e FLASK_APP=superset superset flask fab create-db
#docker-compose run --rm superset ./docker-init.sh

echo "Setting up the database for the dashboard viewer app"
#docker-compose run --rm dashboard_viewer ./docker-init.sh
