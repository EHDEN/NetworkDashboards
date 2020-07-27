# Setup a docker environment

1. Create a `.env` file on this directory, using `.env-example` as reference, setting all necessary environment variables

2. Setup superset

   2.1 Clone the repository to the root of the repository into a directory called ''superset': `git clone https://github.com/apache/incubator-superset ../superset`

   2.2 Checkout to tag 0.37.0rc3: `cd ../superset && git checkout tags/0.37.0rc3 -b tag0.37.0rc3`

   2.3 Create a `docker-init.sh` file on `docker/superset` based on the file `docker/superset/docker-init-example.sh` to set up admin creadencials for superset

3. Set up the database for the dashboard viewer app: `docker-compose run --rm dashboard ./docker-init.sh`

4. Bring up the containers: `docker-compose up`
