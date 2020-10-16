#!/usr/bin/env bash

set -e

echo_step() {
cat <<EOF

######################################################################


[${1}] -- ${2}


######################################################################

EOF
}

source .env

# Import datashboards
echo_step "Starting" "Importing dashboards"

docker cp superset/one_time_run_scripts/dashboards.json ${COMPOSE_PROJECT_NAME}_superset_1:/tmp
docker exec ${COMPOSE_PROJECT_NAME}_superset_1 superset import-dashboards -p /tmp/dashboards.json

echo_step "Complete" "Importing dashboards"
