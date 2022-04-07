# Backups

1. Create a credentials file (the structure of the file depends on the target cloud server)

2. Create a `backups.conf` under the `backups` directory using `backups.conf.example` as base, setting the appropriate value for the several variables.
   
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

### Restore {-}

1. Select the compressed backup you want to restore.

2. Make sure that all the environment variables are the same as the ones that were used for the chosen backup file.
   Additionally, the `backups.conf` file is also necessary to set up, since the `TMP_DIRECTORY` variable will be used.

3. Run the `backups/restore.sh` script.

### Useful stuff {-}

- How to create a shared link to a dropbox directory using its python's API:

   ```sh
   pip install dropbox
   ```

   ```python
   import dropbox
   d = dropbox.Dropbox(API_TOKEN)

   # create a shared link for a directory
   from dropbox.sharing import SharedLinkSettings
   sharing_settings = SharedLinkSettings(
       require_password=True,
       link_password=DIRECTORY_PASSWORD,
   )
   d.sharing_create_shared_link_with_settings(
       DIRECTORY_PATH,
       sharing_settings,
   )

   # get all links
   for link in d.sharing_get_shared_links().links:
       print(f"{link.path} -> {link.url}")
   ```
