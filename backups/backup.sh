#!/bin/sh

STEP_COUNT=7

echo_step() {
  printf "%3s/%s %s\n" "$1" "$STEP_COUNT" "$2"
}

set -e

. "$(dirname "$0")/backups.conf"

if [ "$RUN" -eq 0 ] ; then
    echo "run was 0. exitting"
    exit 0
fi

echo_step "1" "Create temporary directory"
BACKUP_DIRECTORY_NAME=dashboards_backups_$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 40)
TMP_BACKUP_DIRECTORY=$TMP_DIRECTORY/$BACKUP_DIRECTORY_NAME

mkdir "$TMP_BACKUP_DIRECTORY"
EXIT_STATUS=0

(
    echo_step "2" "Get into the docker directory"
    PREVIOUS_PWD=$(pwd)
    cd "$(dirname "$0")"
    (
        cd ../docker

        echo_step "3" "Extract Dashboards's database"
        docker-compose exec -T postgres sh -c "pg_dumpall --clean -U \$POSTGRES_USER -l \$POSTGRES_USER" > $TMP_BACKUP_DIRECTORY/postgres.sql

        echo_step "4" "Extract Redis's data"
        LAST_SAVE=$(docker-compose exec -T redis redis-cli -n $CONSTANCE_REDIS_DB LASTSAVE)

        # started redis backup
        docker-compose exec -T redis redis-cli -n $CONSTANCE_REDIS_DB BGSAVE

        # waiting for redis backup
        while [ "$LAST_SAVE" = "$(docker-compose exec -T redis redis-cli -n $CONSTANCE_REDIS_DB LASTSAVE)" ] ; do
            sleep 5
        done

        REDIS_CONTAINER_ID=$(docker-compose ps -q redis)

        docker cp -a $REDIS_CONTAINER_ID:/data/dump.rdb "$TMP_BACKUP_DIRECTORY/redis.rdb"

        echo_step "5" "Extract Dashboards's media files"
        MEDIA_ROOT=$(docker-compose exec -T dashboard sh -c """
echo '''from django.conf import settings
print(settings.MEDIA_ROOT, end=\"\")
''' | python manage.py shell 2> /dev/null""")

        # fix MEDIA_ROOT if a relative path is returned
        case $MEDIA_ROOT in
            "/"*) ;;
            *)
                MEDIA_ROOT="/app/$MEDIA_ROOT"
            ;;
        esac

        # copy media files to backup folder
        DASHBOARDS_CONTAINER_ID=$(docker-compose ps -q dashboard)
        docker cp -a $DASHBOARDS_CONTAINER_ID:$MEDIA_ROOT "$TMP_BACKUP_DIRECTORY"

        echo_step "6" "Compress gathered data"
        COMPRESSED_FILE_PATH=$TMP_DIRECTORY/${APP_NAME}_$(date +"%Y%m%d%H%M%S").zip
        (
            cd "$TMP_DIRECTORY"
            zip -q -r "$COMPRESSED_FILE_PATH" $BACKUP_DIRECTORY_NAME
            #tar -C "$TMP_DIRECTORY" -cJf "$COMPRESSED_FILE_PATH" $BACKUP_DIRECTORY_NAME

            echo_step "7" "Send to $SERVER"
            backup_uploader "$APP_NAME" "$SERVER" "$CREDENTIALS_FILE_PATH" "$BACKUP_CHAIN_CONFIG" "$COMPRESSED_FILE_PATH"
        ) || EXIT_STATUS=$?
        rm -f "$COMPRESSED_FILE_PATH"

        exit $EXIT_STATUS
    ) || EXIT_STATUS=$?
    cd "$PREVIOUS_PWD"

    exit $EXIT_STATUS
) || EXIT_STATUS=$?

rm -rf "$TMP_BACKUP_DIRECTORY"

if [ $EXIT_STATUS -ne 0 ] ; then
    echo "Failed with exit code $EXIT_STATUS"
    exit $EXIT_STATUS
fi
