# Backup

1. Create a credentials file (the structure of the file depends on the target cloud server)

2. Create a `.dashboards_backups.conf` file under your home directory (variable `$HOME`) using `dashboards_backups.conf.example` as base, setting the appropriate value for the several variables.
   
   For variables associated with files and directories always use *absolute* paths.
   
   Variables:
   
   - `RUN`: Set it to `0` if you don't want the next scheduled backup to run.
     
     This variable allows you to cancel any backup runs while you are doing some maintenance on the application.

   - `CONSTANCE_REDIS_DB`: Number of the Redis database where the django constance config is stored. The default value is 2. This value should be the same as the environment variable `REDIS_CONSTANCE_DB` of the dashboard container.
   
   - The following variables are associated with the arguemtns of the `backup_uploader` python package. Check its [usage](https://github.com/aspedrosa/BackupUploader#usage) for more details:
   
      - `APP_NAME`: The backup process will generate some directories with this name in places that are shared with other applications.
    
      - `SERVER`: The name of the target cloud server to where backups should be uploaded (dropbox or mega).
    
      - `BACKUP_CHAIN_CONFIG`: Allows having different directories with backups of different ages.
   
      - `CREDENTIALS_FILE_PATH`: File containing the credentials to access the server to upload the backup file.

3. Install the `backup_uploader` python package by following its [install](https://github.com/aspedrosa/BackupUploader#install) instructions.

4. Schedule your backups
   
   ```sh
   *    *    *   *    *  Command_to_execute
   |    |    |    |   |       
   |    |    |    |    Day of the Week ( 0 - 6 ) ( Sunday = 0 )
   |    |    |    |
   |    |    |    Month ( 1 - 12 )
   |    |    |
   |    |    Day of Month ( 1 - 31 )
   |    |
   |    Hour ( 0 - 23 )
   |
   Min ( 0 - 59 ) 
   ```
   
   (Retrived from: [Tutorialspoint](https://www.tutorialspoint.com/unix_commands/crontab.htm))
   
   Ex: To run every day at 3:00 am
   
   1. `crontab -e`
   
   2. Add entry `0 3 * * * $HOME/NetworkDashboards/backups/backup.sh` (The path to the backup script might be different)

### Restore

1. Select the compressed backup you want to restore and decompress it:
   
   `tar -xJf BACKUP_FILE.tar.xz`.

2. 1. **Redis**
      
      1. Make sure the redis docker container is down.
      
      2. (Re)place the file `dump.rdb` on the redis volume by the file `redis.rdb`. By default the redis volume is located where this repository was cloned on the directory `docker/volumes/redis`.
      
      3. Change its permissions, owner and group:
         
         ```shell
         chmod 0644 docker/volumes/redis/dump.rdb
         sudo chown -R 999:999 docker/volumes/redis
         ```
   
   2. **Postgres**
      
      1. Make sure all containers that make changes on the database are stopped.
      
      2. Copy the file `postgres_backup.sql` into the postgres container
         
         `docker cp postgres.sql [CONTAINER_ID]:/tmp`.
      
      5. Execute the backup script:
         
         `docker exec -u root dashboard_viewer_postgres_1 psql -f /tmp/postgres_backup.sql -U \$POSTGRES_USER -d \$POSTGRES_DB`.
   
   3. **Media Files** If you have a volume pointing to where the media files are stored, replace all files with the ones present on the downloaded backup file. Else:
   
      1. Bring the dashoard container up `docker-compose up -d dashboard`
      
      2. Enter in the container `docker exec -it [CONTAINER_ID] bash`
      
      3. If you don't know where the media files are stored you can check the value of the MEDIA_ROOT variable
         
         1. `python manage.py shell`
         
         2. `from django.conf import settings`
         
         3. `print(settings.MEDIA_ROOT)`
      
      4. Remove the entire MEDIA_ROOT directory and exit the container
      
      5. Copy the media directory present on the backup file to the catalogue container `docker cp -a collected-media [CONTAINER_ID]:[MEDIA_ROOT_PARENT_PATH]`
