# Setup a docker environment

1. Create a `.env` file here, using `.env-example` as reference,
setting all necessary environment variables

2. Setup superset

    2.1. Clone the repository
    
    `git clone https://github.com/apache/incubator-superset ../superset`

    2.2 Checkout to tag 0.35.1

    `cd ../superset && git checkout tags/0.35.1 -b tag0.35.1`

3. Set up the database for superset

    `docker-compose run --rm superset ./docker-init.sh`

4. Set up the database for the dashboard viewer app

    `docker-compose run --rm dashboard_viewer ./docker-init.sh`

4. Bring up the containers

    `docker-compose up -d`
