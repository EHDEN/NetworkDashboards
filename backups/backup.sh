#!/bin/sh

set -e

. $HOME/.dashboards_backups.conf

if [ $RUN -eq 0 ] ; then
    echo "run was 0. exitting"
    exit 0
fi


BACKUP_DIRECTORY_NAME=dashboards_backups_$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 40)
TMP_BACKUP_DIRECTORY=/tmp/$BACKUP_DIRECTORY_NAME

mkdir $TMP_BACKUP_DIRECTORY

# 2. Get into the docker directory
previous_pwd=$(pwd)
cd $(dirname "$0")
cd ../docker

# postgres
echo "getting postgres backup"
docker-compose exec postgres sh -c "pg_dumpall -c -U \$POSTGRES_USER" > $TMP_BACKUP_DIRECTORY/postgres.sql

# redis
LAST_SAVE=$(docker-compose exec redis redis-cli -n $CONSTANCE_REDIS_DB LASTSAVE)

echo "started redis backup"
docker-compose exec redis redis-cli -n $CONSTANCE_REDIS_DB BGSAVE

echo "waiting for redis backup"
while [ "$LAST_SAVE" = "$(docker-compose exec redis redis-cli -n $CONSTANCE_REDIS_DB LASTSAVE)" ] ; do
    sleep 5
done

REDIS_CONTAINER_ID=$(docker-compose ps -q redis)

docker cp -a $REDIS_CONTAINER_ID:/data/dump.rdb $TMP_BACKUP_DIRECTORY/redis.rdb

# media files
MEDIA_ROOT=$(docker-compose exec dashboard sh -c """
echo '''from django.conf import settings
print(settings.MEDIA_ROOT, end=\"\")
''' | python manage.py shell""")

# fix MEDIA_ROOT if a relative path is returned
case $MEDIA_ROOT in
    "/"*) ;;
    *)
        MEDIA_ROOT="/app/$MEDIA_ROOT"
    ;;
esac

echo "copy media files to backup folder"
DASHBOARDS_CONTAINER_ID=$(docker-compose ps -q dashboard)
docker cp -a $DASHBOARDS_CONTAINER_ID:$MEDIA_ROOT $TMP_BACKUP_DIRECTORY

# compression
COMPRESSED_FILE_PATH=/tmp/$(date +"%Y%m%d%H%M%S").tar.xz
echo "compressing files"
tar -C /tmp -cJf $COMPRESSED_FILE_PATH $BACKUP_DIRECTORY_NAME

# send to server
echo "sending to backup server"
backup_uploader $APP_NAME $SERVER $CREDENTIALS_FILE_PATH $BACKUP_CHAIN_CONFIG $COMPRESSED_FILE_PATH

# remove temporaty files
echo "removing backup temporary files"
rm -r $TMP_BACKUP_DIRECTORY
rm $COMPRESSED_FILE_PATH
