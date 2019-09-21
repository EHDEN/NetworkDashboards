#!/bin/bash

set -ex

# TODO create two cases: production and development

python manage.py runserver 0.0.0.0:8000
