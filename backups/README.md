# Backup

1. Create a credentials file with the following structure:
   
   ```
   usename@mail.com
   password
   ```
   
   Insert the credentials to the server to upload the backup file.

2. Create a `.dashboards_backup.conf` file under your home directory (variable `$HOME`) using `.dashboards_backup.conf.example` as base, setting the appropriate value for the several variables.
   
   For variables associated with files and directories always use *absolute* paths.
   
   Variables:
   
   - `RUN`: Set it to `0` if you don't want the next scheduled backup to run.
     
     This variables allows you to cancel any backup runs while you are doing some maintenance on the application.
   
   - `ACHILLES_RESULTS_FILES_DIRECTORY`: The directory where the dashboard app is storing the achilles results files. By default the is located where this repository was cloned on the directory `docker/volumes/achilles_results_files`.
   
   - `UPLOAD_TO_SERVER_SCRIPT_PATH`: A script that receives the path to the credentials file and the backup file to upload to the server. Currently we developed a script to upload to [Mega](https://mega.nz/), to use it this variable should point to the `upload_to_server.py` on this folder.
   
   - `CREDENTIALS_FILE_PATH`: File containing the credentials to access the server to upload the backup file.

3. Install mega python package: `pip install mega.py`.

4. Create a directory `dashboards_backups` under `/var/lib` and create a file named `counters.json`. Change counters file permissions: `chmod 0666 counters.json`.

5. Schedule your backups
   
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

# Restore

1. Select the compressed backup you want to restore an decompress it:
   
   `tar -xvJf BACKUP_FILE.tar.xz`.

2. 1. **Redis**
      
      1. Make sure the redis docker container is down.
      
      2. (Re)place the file `dump.rdb` on the redis volume by the file `redis_backup.rdb`. By default the redis volume is located where this repository was cloned on the directory `docker/volumes/redis`.
      
      3. Change its permissions, owner and group:
         
         ```shell
         chmod 0644 docker/volumes/redis/dump.rdb
         sudo chown -R 999:999 docker/volumes/redis
         ```
   
   2. **Postgres**
      
      1. Make sure the postgres container is down.
      
      2. Remove postgres volume. By default it is located where this repository was cloned on the directory `docker/volumes/postgres`.
      
      3. Bring the postgres container up:
         
         `docker-compose up -d postgres`.
      
      4. Copy the file `postgres_backup.sql` into the postgres container
         
         `docker cp postgres_backup.sql dashboard_viewer_postgres_1:/tmp`.
      
      5. Execute the backup script:
         
         `docker exec -u root dashboard_viewer_postgres_1 psql -f /tmp/postgres_backup.sql postgres`.
   
   3. **Achilles Results Files**
      
      1. Replace all directories under `achilles_results_files_backup` to  the `achilles_results_files` volume directory. By default the `achilles_results_files` volume directory is located where this repository was cloned on the directory `docker/volumes`.
      
      2. Change owner and group:
         
         `chown -R root:root docker/volumes/achilles_results_files`.
