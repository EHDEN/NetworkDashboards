#!/usr/bin/env bash

# Based on https://github.com/apache/incubator-superset/blob/0.37.0rc3/docker/docker-init.sh

set -e

STEP_CNT=2

echo_step() {
cat <<EOF

######################################################################


Init Step ${1}/${STEP_CNT} [${2}] -- ${3}


######################################################################

EOF
}

# Initialize the database
echo_step "1" "Starting" "Applying DB migrations"
superset db upgrade
echo_step "1" "Complete" "Applying DB migrations"

# Create default roles and permissions
echo_step "2" "Starting" "Setting up roles and perms"
superset init
echo_step "2" "Complete" "Setting up roles and perms"
