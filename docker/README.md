# Setup a docker environment

## First Steps

1. Clone the repository with the command `git clone --recurse-submodules https://github.com/EHDEN/NetworkDashboards`. If you already cloned the repository without the `--recurse-submodules` option, run `git submodule update --init` to fetch the superset submodule.

2. Create a `.env` file on the `docker` directory, using `.env-example` as a reference, setting all necessary environment variables (`SUPERSET_MAPBOX_API_KEY` and `DASHBOARD_VIEWER_SECRET_KEY`).

## Dashboard Viewer setup

1. If you wish to expose the dashboard viewer app through a specific domain(s) you must add it/them to the `ALLOWED_HOSTS` list on file `dashboard_viewer/dashboard_viewer/settings.py` and remove the `'*'` entry.

2. Build containers' images: `docker-compose build`. This might take several minutes.

3. Set up the database and create an admin account for the dashboard viewer app: `docker-compose run --rm dashboard ./docker-init.sh`.

## Insert Concepts

The concepts table is not in the repository due to its dimension, therefore we use directly the Postgres console to insert this table in the installation.

1. Get your concept csv file from [Athena](https://athena.ohdsi.org/)

2. Copy the file into postgres container

   ```sh
   docker cp concept.csv dashboard_viewer_postgres_1:/tmp/
   ```

3. Enter in the postgres container:

   ```sh
   docker exec -it dashboard_viewer_postgres_1 bash
   ```

4. Enter in the `achilles`  database (value of the variable `POSTGRES_ACHILLES_DB` on the .env file) with the `root` user (value of the variable `POSTGRES_ROOT_USER` on the .env file):

   ```
   psql achilles root
   ```

5. Create the `concept` table

   ```sql
   CREATE TABLE concept (
     concept_id         INTEGER        NOT NULL,
     concept_name       VARCHAR(255)   NOT NULL,
     domain_id          VARCHAR(20)    NOT NULL,
     vocabulary_id      VARCHAR(20)    NOT NULL,
     concept_class_id   VARCHAR(20)    NOT NULL,
     standard_concept   VARCHAR(1)     NULL,
     concept_code       VARCHAR(50)    NOT NULL,
     valid_start_date   DATE           NOT NULL,
     valid_end_date     DATE           NOT NULL,
     invalid_reason     VARCHAR(1)     NULL
   );
   ```

6. Copy the CSV file content to the table (this could take a while)

   To get both `'` (single quotes) and `"` (double quotes) on the `concept_name` column we use a workaround by setting the quote character to one that should never be in the text. Here we used `\b` (backslash).

   ```sql
   COPY public.concept FROM '/tmp/concept.csv' WITH CSV HEADER
     DELIMITER E'\t' QUOTE E'\b';
   ```

7. Create index in table (this could take a while):

   ```sql
   CREATE INDEX concept_concept_id_index ON concept (concept_id);
   CREATE INDEX concept_concept_name_index ON concept (concept_name);
   ```

8. Set the owner of the `concept` table to the `achilles` user (value of the variable `POSTGRES_ACHILLES_USER` on the .env file):

   ```
   ALTER TABLE concept OWNER TO achiller
   ```

9. Bring up the containers: `docker-compose up -d`.

10. Run the command `docker-compose run --rm dashboard python manage.py generate_materialized_views` to create the materialized views on Postgres.

## Superset setup

1. Make sure that the container `superset-init` has finished before continuing. It is creating the necessary tables on the database and creating permissions and roles.

2. Execute the script `./superset/one_time_run_scripts/superset-init.sh`. This will create an admin account and associate the `achilles` database to Superset. **Attention:** You must be in the docker directory to execute this script.

3. We have already built some dashboards so if you want to import them run the script `./superset/one_time_run_scripts/load_dashboards.sh`. **Attention:** You must be in the docker directory to execute this script.

4. If you used the default ports:

   - Go to `http://localhost` to access the dashboard viewer app.
   - Go to `http://localhost:8088` to access superset.

5. On release 0.37 of Superset, there is a bug related to the public role and because of that, we had to set `PUBLIC_ROLE_LIKE_GAMMA = True` on Superset settings. This leads the public role with permissions that he shouldn't have. To solve this, so any anonymous user can view dashboards, you should remove all its permissions and then add the following:

   - can explore JSON on Superset
   - can dashboard on Superset
   - all datasource access on all_datasource_access
   - can csrf token on Superset
   - can list on CssTemplateAsyncModelView

## Dummy data

On a fresh installation, there are no achilles_results data so Superset's dashboards will display "No results". On the root of this repository, you can find the `demo` directory where we have an ACHILLES results file with synthetic data that you can upload to a data source on the uploader app of the dashboard viewer (localhost/uploader). If you wish to compare multiple data sources, on the `demo` directory the is also a python script that allows you to generate new ACHILLES results files, where it generates random count values based on the ranges of values for each set of analysis_id and stratums present on a base ACHILLES results file. So, from the one ACHILLES results fill we provided, you can have multiple data sources with different data.
