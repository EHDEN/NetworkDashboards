# Tests

## Develop

If you want to develop tests for the Django app you will need to have both Redis and Postgres running.
On the `tests/` directory there is a docker-compose file that will launch a Redis and a Postgres container both with open ports and with no volumes.
This way you can execute your tests through your IDE, such as PyCharm, and take advantage of its debugger while developing tests.
However, under the hood, the IDE is running commands such as `python manage.py tests uploader.UploaderRestrictedAccess`.

You will also need to set some environment variables either on the IDE or before executing `python manage.py tests ...` commands:
```sh
POSTGRES_DEFAULT_HOST=localhost
POSTGRES_ACHILLES_HOST=localhost
SECRET_KEY=test
DJANGO_SETTINGS_MODULE=dashboard_viewer.settings
REDIS_HOST=localhost
```

## Run

tox is a good way to run all test commands without having to install the test requirements for each test case (code style checks, unit tests, ...). tox will create a tox environment, install the necessary dependencies for each case and run the test command.

tox and its dependencies are in the file `requirements-dev/requirements-dev.txt`. After installing them you just need to execute `tox` to run all the test cases. To run a specific test case execute for example `tox -e black`. To make the `test*` cases pass you will need the docker-compose stack mentioned in the previous section up.

