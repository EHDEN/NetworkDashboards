#!/usr/bin/env bash

# Based on https://github.com/apache/incubator-superset/blob/0.37.0rc3/docker/docker-init.sh

set -e

STEP_CNT=5

echo_step() {
cat <<EOF

######################################################################


Init Step ${1}/${STEP_CNT} [${2}] -- ${3}


######################################################################

EOF
}

# Create an admin user - >> CHANGE THE VALUES BELOW <<
echo_step "1" "Starting" "Setting up admin user ( admin / admin )"
superset fab create-admin \
              --username admin \
              --firstname Superset \
              --lastname Admin \
              --email admin@superset.com \
              --password admin
echo_step "1" "Complete" "Setting up admin user"

# Initialize the database
echo_step "2" "Starting" "Applying DB migrations"
superset db upgrade
echo_step "2" "Complete" "Applying DB migrations"

# Create default roles and permissions
echo_step "3" "Starting" "Setting up roles and perms"
superset init
echo_step "3" "Complete" "Setting up roles and perms"

# Import Achilles datasource
echo_step "4" "Starting" "Importing datasources"
sed -e "s/ACHILLES_HOST/$ACHILLES_DATABASE_HOST; s/ACHILLES_PORT/$ACHILLES_DATABASE_PORT; s/ACHILLES_DB/$ACHILLES_DATABASE_DB; s/ACHILLES_USER/$ACHILLES_DATABASE_USER; s/ACHILLES_PASSOWRD/$ACHILLES_DATABASE_PASSWORD/" /app/data/datasources.yaml > /tmp/datasources.yaml
superset import-datasources -p /tmp/datasources.yaml
echo_step "4" "Complete" "Importing datasources"

# Import datashboards
echo_step "5" "Starting" "Importing dashboards"
superset import-dashboards -p /app/data/dashboards.json
echo_step "5" "Complete" "Importing dashboards"
