# cdm-bi
Tool for business intelligence using OMOP CDM

## Installation

Make sure that you have docker and docker-compose installed in your machine. Then, please follow these steps:

- Please enter in the ''docker'' directory and create your `.env` file here, using `.env-example` as reference. For local installation, you can just copy the `.env-example` content to a new file. Note: In case of port errors in the next steps, the problem could be related to a port already in use by your system that you defined here and it is busy, chose other.
- Tip the following commands in the command line:
    1. Clone the Apache Superset repository:
        ```
        git clone https://github.com/apache/incubator-superset ../superset
        cp ../superset/contrib/docker/superset_config.py ../superset
        ```
    2. Init the Apache Superset (This creates a user, so it is necessary to interact with the console):
        ```
        docker-compose run --rm -e FLASK_APP=superset superset flask fab create-db
        docker-compose run --rm superset ./docker-init.sh
        ```
    3. Init the Dashboard Layout  (This creates a user, so it is necessary to interact with the console):
        ```
        docker-compose run --rm dashboard_viewer ./docker-init.sh
        ```
    4. Finally, bring up the containers 
        ```
        docker-compose up -d
        ```
        
To check if everything is ok, please wait 2 minutes and tip `docker ps` and the following containers need to be running: 
```
... 0.0.0.0:8088->8088/tcp   dashboard_viewer_superset_1
... 0.0.0.0:8000->8000/tcp   dashboard_viewer_dashboard_viewer_1
... 0.0.0.0:6379->6379/tcp   dashboard_viewer_redis_1
... 5432/tcp                 dashboard_viewer_postgres_1
```

Now, you have a clean setup running in your machine. To try the application using synthetic data, please continue to follow the steps in the ''Demo'' section.

## Demo

1. Reconfigure the database on Superset (`localhost:8088`) to upload csvs.
- Go to "Sources"-> "Databases" and edit the existing
database (Second icon on the left).
- Check the checkbox on "Expose in SQL Lab" and "Allow
Csv Upload ".

2. For each *CSV file* on the `demo/` folder:
- Go to "Sources" -> "Upload a CSV"
- Set the name of the table equal to the name of the file uploading without the extension
- Select the csv file
- Choose the database configured on the previous step

3. Upload the exported dashboard file
- Go to "Manage" -> "Import Dashboards"
- Select the `sources_by_age_dashboard_exported.json` file,
present on the `demo/` folder.
- Click "Upload"

4. Add a new tab to the dashboard viewer app.
- Go to the Django's admin app (`localhost:8000/admin`)
- On the `DASHBOARD_VIEWER` section and on `Tabs`
row, add a new Tab.
- Fill form's fields
```
Title:    Sources by age
Icon:     birthday-cake
Url:      See the next point
Position: 1
Visible:  ✓
```
- To get the url field
    - Go back to superset (`localhost:8088`)
    - Go to "Dashboards"
    - Right click on the dashboard "Sources by age" and copy the link address
    - Go back to the dashboard viewer app
    - Paste de link and append to it `?standalone=true`
    - Save
    
5. Update the public permissions to see the dashboards
- In Superset go to "Security" -> "List Roles"
- Select the "Edit record" button from the public role.
- In the Permissions field, add the following categories:
    - can explore JSON on Superset
    - can dashboard on Superset
    - all datasource access on all_datasource_access
    - can csrf token on Superset

6. Now you can go back to the root url (`localhost:8000`) to see the final result
