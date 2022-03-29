#!/bin/sh

set -e

if [ $# -ne 1 ] ; then
  1>&2 echo "Usage: restore.sh [zip backup file]"
  exit 1
fi

STEP_COUNT=5

echo_step() {
  printf "%3s/%s %s\n" "$1" "$STEP_COUNT" "$2"
}

. "$(dirname "$0")/backups.conf"

echo_step 1 "Extracting backup file"

BACKUP_ROOT_DIRECTORY=$(unzip -qql $1 | head -n1 | sed -r '1 {s/([ ]+[^ ]+){3}\s+//;q}')
unzip $1 -d "$TMP_DIRECTORY" >/dev/null
BACKUP_ROOT_DIRECTORY="$TMP_DIRECTORY/$BACKUP_ROOT_DIRECTORY"

EXIT_STATUS=0

(
  echo_step 2 "Get into the docker directory"
  PREVIOUS_PWD=$(pwd)
  cd $(dirname "$0")
  (
    cd ../docker

    echo_step 3 "Restoring postgres"
    docker-compose stop dashboard dashboard_worker superset superset-worker superset-worker-beat >/dev/null 2>&1
    docker-compose up -d postgres >/dev/null 2>&1

    until docker-compose exec -T postgres sh -c "pg_isready" >/dev/null 2>&1 ; do
        sleep 2
    done

    CONTAINER_ID=$(docker-compose ps -q postgres)
    docker cp $BACKUP_ROOT_DIRECTORY/postgres.sql $CONTAINER_ID:/tmp
    docker-compose exec -T postgres sh -c """
psql -f /tmp/postgres.sql -U \$POSTGRES_USER -d postgres
rm /tmp/postgres.sql
"""

    echo_step 4 "Restoring redis"
    docker-compose up -d redis >/dev/null 2>&1
    CONTAINER_ID=$(docker-compose ps -q redis)
    docker cp $BACKUP_ROOT_DIRECTORY/redis.rdb $CONTAINER_ID:/
    docker-compose exec -T redis sh -c """
mv /redis.rdb /data
"""
    docker-compose restart redis >/dev/null 2>&1

    echo_step 5 "Restoring Dashboards' media files"
    docker-compose up -d dashboard >/dev/null 2>&1
    MEDIA_ROOT=$(docker-compose exec -T dashboard sh -c """
echo '''from django.conf import settings
print(settings.MEDIA_ROOT, end=\"\")
''' | python manage.py shell 2>/dev/null""")

    # fix MEDIA_ROOT if a relative path is returned
    case $MEDIA_ROOT in
        "/"*) ;;
        *)
            MEDIA_ROOT="/app/$MEDIA_ROOT"
        ;;
    esac

    CONTAINER_ID=$(docker-compose ps -q dashboard)

    docker-compose exec -T dashboard sh -c """
cd $MEDIA_ROOT
find . -mindepth 1 -maxdepth 1 -exec rm -r {} +
"""
    docker cp -a $BACKUP_ROOT_DIRECTORY/$(basename $MEDIA_ROOT) $CONTAINER_ID:$MEDIA_ROOT
    docker-compose exec -T dashboard sh -c """
cd $MEDIA_ROOT
find $(basename $MEDIA_ROOT) -mindepth 1 -maxdepth 1 -exec mv -t . -- {} +
rmdir $(basename $MEDIA_ROOT)
"""

    docker-compose up -d
  ) || EXIT_STATUS=$?
  cd $PREVIOUS_PWD

  exit $EXIT_STATUS
) || EXIT_STATUS=$?
#rm -rf "$BACKUP_ROOT_DIRECTORY"

if [ $EXIT_STATUS -ne 0 ] ;then
    echo "Failed with exit code $EXIT_STATUS"
    exit $EXIT_STATUS
fi
