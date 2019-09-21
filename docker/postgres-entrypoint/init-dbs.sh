#!/bin/bash

# Script to create several databases with a user associated
#  on the postgres container before he starts to accept connections

set -ex

if [ -n "$POSTGRES_DBS" ] ; then
  # Create arrays with information for the several databases to create
  # Received through docker-compose environment variables
  declare -a DBS=($POSTGRES_DBS)
  declare -a USERS=($POSTGRES_DBS_USERS)
  declare -a PASSWORDS=($POSTGRES_DBS_PASSWORDS)

  # Check if all arrays have the same lenght
  if ! [ ${#USERS[@]} -eq ${#DBS[@]} ] || ! [ ${#DBS[@]} -eq ${#PASSWORDS[@]} ] ; then
    echo "Different size of the variables POSTGRES_DBS, POSTGRES_DBS_USERS and POSTGRES_DBS_PASSWORDS"
    exit 1
  fi

  for i in $(seq 0 $((${#DBS[@]}-1)) ) ; do
    DB=${DBS[$i]}
    USER=${USERS[$i]}
    PASSWORD=${PASSWORDS[$i]}

    psql -c "CREATE USER $USER WITH PASSWORD '$PASSWORD'" -U root
    psql -c "CREATE DATABASE $DB" -U root
    psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB TO $USER" -U root
  done
fi
