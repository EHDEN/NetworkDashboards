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

source .env

echo_step "1" "Starting" "Setting up admin user"
docker-compose run superset superset fab create-admin \
              --username $SUPERSET_ADMIN_USERNAME \
              --password $SUPERSET_ADMIN_PASSWORD \
              --firstname $SUPERSET_ADMIN_FIRSTNAME \
              --lastname $SUPERSET_ADMIN_LASTNAME \
              --email $SUPERSET_ADMIN_EMAIL
echo_step "1" "Complete" "Setting up admin user"

# Import Achilles datasource
echo_step "2" "Starting" "Importing datasources"

docker-compose run superset sh -c "echo 'import sqlalchemy
import sys
from superset import db
from superset.models.core import Database

achilles_db = Database(database_name=\"Achilles\")
achilles_db.set_sqlalchemy_uri(\"postgresql+psycopg2://$POSTGRES_ACHILLES_USER:$POSTGRES_ACHILLES_PASSWORD@postgres:5432/$POSTGRES_ACHILLES_DB\")

db.session.add(achilles_db)
try:
    db.session.commit()
except sqlalchemy.exc.IntegrityError:
    print(\"Achilles database already exists\")
except:
    sys.exit(1)

' | flask shell"

echo_step "2" "Complete" "Importing datasources"
