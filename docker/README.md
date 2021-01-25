# Setup a docker environment

1. Clone the repository with the command `git clone --recurse-submodules https://github.com/EHDEN/NetworkDashboards`. If you already cloned the repository without the `--recurse-submodules` option, run `git submodule update --init` to fetch the superset submodule.

2. Create a `.env` file on the `docker` directory, using `.env-example` as reference, setting all necessary environment variables (SUPERSET\_MAPBOX\_API\_KEY and DASHBOARD\_VIEWER\_SECRET\_KEY).

3. Create a `docker-init.sh` file on `docker/superset` based on the file `docker/superset/docker-init-example.sh` to set up admin credentials for superset.

4. If you wish to expose the dashboard viewer app through a specific domain(s) you must add it/them to the ALLOWED_HOSTS list on file `dashboard_viewer/dashboard_viewer/settings.py` and remove the `'*'` entry.

5. Build containers' images: `docker-compose build`. This might take several minutes.

6. Set up the database for the dashboard viewer app: `docker-compose run --rm dashboard ./docker-init.sh`.

7. Bring up the containers: `docker-compose up -d`.

8. If you used the default ports:

   - Go to `http://localhost` to access the dashboard viewer app.
   - Go to `http://localhost:8088` to access superset.

9. To any anonymous user view dashboards, add the following:

   - all datasource access on all_datasource_access
   - can csrf token on Superset
   - can dashboard on Superset
   - can explore json on Superset
   - can read on Chart
   - can read on CssTemplate