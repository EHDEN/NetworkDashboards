# Setup a docker environment

1. Clone the repository with the command `git clone --recurse-submodules https://github.com/EHDEN/NetworkDashboards`. If you already cloned the repository without the `--recurse-submodules` option, run `git submodule update --init` to fetch the superset submodule.

2. Create a `.env` file on the `docker` directory, using `.env-example` as a reference, setting all necessary environment variables (SUPERSET\_MAPBOX\_API\_KEY and DASHBOARD\_VIEWER\_SECRET\_KEY).

3. If you wish to expose the dashboard viewer app through a specific domain(s) you must add it/them to the ALLOWED_HOSTS list on file `dashboard_viewer/dashboard_viewer/settings.py` and remove the `'*'` entry.

4. Build containers' images: `docker-compose build`. This might take several minutes.

5. Set up the database for the dashboard viewer app: `docker-compose run --rm dashboard ./docker-init.sh`.

6. Bring up the containers: `docker-compose up -d`.

7. Wait until the container `superset-init` stops running. It is creating the necessary tables on the database and creating permissions and roles.

8. Execute the script `./superset/one_time_run_scripts/superset-init.sh`. This will create an admin account and associate the `achilles` database to Superset. **Attention:** You must be in the docker directory to execute this script.

9. We have already built some dashboard so if you want to import them run the script `./superset/one_time_run_scripts/load_dashboards.sh`. **Attention:** You must be in the docker directory to execute this script.

10. If you used the default ports:

    - Go to `http://localhost` to access the dashboard viewer app.
    - Go to `http://localhost:8088` to access superset.

11. On release 0.37 of superset there is a bug related to the public role and because of that, we had to set `PUBLIC_ROLE_LIKE_GAMMA = True` on superset settings. This leads the public role with permissions that he shouldn't have. To solve this, so any anonymous user can view dashboards, you should remove all its permissions and then add the following:

    - can explore JSON on Superset
    - can dashboard on Superset
    - all datasource access on all_datasource_access
    - can csrf token on Superset
    - can list on CssTemplateAsyncModelView
