#!/bin/sh

. $HOME/.dashboards_backup.conf

if [ $RUN -eq 0 ] ; then
    echo "run was 0. exitting"
    exit 0
fi


BACKUP_DIRECTORY_NAME=dashboards_backups_$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 40)
TMP_BACKUP_DIRECTORY=/tmp/$BACKUP_DIRECTORY_NAME

mkdir $TMP_BACKUP_DIRECTORY

# postgres
echo "getting postgres backup"
docker exec dashboard_viewer_postgres_1 pg_dumpall > $TMP_BACKUP_DIRECTORY/postgres_backup.sql

# redis
LAST_SAVE=$(docker exec dashboard_viewer_redis_1 redis-cli LASTSAVE)

echo "started redis backup"
docker exec dashboard_viewer_redis_1 redis-cli BGSAVE

echo "waiting for redis backup"
while [ $LAST_SAVE -eq $(docker exec dashboard_viewer_redis_1 redis-cli LASTSAVE) ] ; do
    sleep 5
done

docker cp dashboard_viewer_redis_1:/data/dump.rdb $TMP_BACKUP_DIRECTORY/redis_backup.rdb

# achilles results files
echo "copy achilles results files to backup folder"
cp -r $ACHILLES_RESULTS_FILES_DIRECTORY $TMP_BACKUP_DIRECTORY/achilles_results_files_backup

# compression
COMPRESSED_FILE_PATH=/tmp/$(date +"%Y%m%d%H%M%S").tar.xz
echo "compressing files"
tar -C /tmp -cvJf $COMPRESSED_FILE_PATH $BACKUP_DIRECTORY_NAME

# send to server
echo "sending to backup server"
$UPLOAD_TO_SERVER_SCRIPT_PATH $CREDENTIALS_FILE_PATH $COMPRESSED_FILE_PATH

# remove temporaty files
echo "removing backup temporary files"
rm -r $TMP_BACKUP_DIRECTORY
rm $COMPRESSED_FILE_PATH
