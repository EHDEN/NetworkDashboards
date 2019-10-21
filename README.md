# cdm-bi
Tool for business intelligence using OMOP CDM

## Installation

Make sure that you have docker and docker-compose installed in your machine. The, please follow these steps:

- Please enter in the ''docker'' directory and this directory create your `.env` file here, using `.env-example` as reference. For local installation, you can just copy the `.env-example` content to a new file. Note: In case of port errors in the next steps, the problem could be related to a port already in use by your system that you defined here and it is busy, chose other.
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

- TO DO