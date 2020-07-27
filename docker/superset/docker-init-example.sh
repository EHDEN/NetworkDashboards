#!/usr/bin/env bash

# Based on https://github.com/apache/incubator-superset/blob/0.37.0rc3/docker/docker-init.sh

set -e

STEP_CNT=3

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
