# Setup a docker environment

1. Create a `.env` file here, using `.env-example` as reference,
setting all necessary environment variables

2. Create a `SECRET_KEY.py` file on `../dashboard_viewer`
with the content `SECRET_KEY="my_secret_key"`

3. Run the setup script `./setup.sh`

4. Bring up the containers `docker-compose up`
