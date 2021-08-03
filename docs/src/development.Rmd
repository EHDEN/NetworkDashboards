# Development Instructions

### Repository Structure Description {-}

- backups: Scripts and configuration files to perform backups of all the data involved in the Network Dashboards applications (Dashboard viewer + Superset)

- dashboard_viewer: The Dashboard Viewer Django application to manage and upload catalogue results data. More detail can be found in the [Code Documentation](code-documentation.html) chapter.

- demo: Files that can be used to test some processes of the platform (Upload catalogue results data and import a simple dashboard)

- docker: Docker-compose stack-related directories.
  - Environment file
  - Configuration directories (Nginx and Postgres)
  - Custom Superest Dockerfile <!-- TODO link to the subsection on the Superset section -->

  For more information about docker deployment consult the [Installation](installation.html) chapter.

- docs: Where the files of this gitbook are hosted. Other output formats can also be obtained here. Consult the [Documentation](development-instructions.html#documentation) section of this chapter for more details.

- superset: contains a submodule to the latest supported version  of Superset's repository and our custom chart plugins

- tests: contains files to launch a docker-compose stack specific to run tests.

- requirements-dev: python requirements files to the several tools to either perform code style checks or to run Django tests

- .pre-commit-config.yaml: configuration for the [pre-commit](https://pre-commit.com/) tool. This is not mandatory to use but is a good tool to automatically fix problems related to code style on staged files

- setup.cfg: configurations for the several code style tools

- tox.ini: configuration for the [tox](https://tox.readthedocs.io/) tool. It helps automate the process to check if the code style is correct and if the Django tests are passing

  It's extremely useful in this context since different code style check tools that we use have some conflicts with python dependencies. It creates a virtual environment for each tox environment, in our case, for each code style check tool plus Django tests

### Superset {-}

### Github Actions {-}

### Tests {-}

### Python Requirements {-}

The python requirements for the Dashboard Viewer Django app are present on the `requirements.txt` file of the `dashboard_viewer` directory.
The file is divided into two sections.
First are the direct dependencies.
Dependencies that are directly used or imported by the Dashboard Viewer Django app.
For better maintainability, every direct dependency has a small description in front of it, so any developer knows why it is being mentioned in the requirements file.
The second part of the file contains the indirect dependencies.
Basically dependencies of our direct dependencies.

After any update is made to the direct dependencies the following procedure should be followed:

1. Create a new virtual environment just for the dependencies of this file
2. Delete the indirect dependencies section of the file
3. Install all the direct dependencies `pip install -r requirements.txt`
4. Append the result of pip's freeze to the requirements file `pip freeze >> requirements.txt`
5. Remove from the second section of the file, duplicated entries of the first section of the file, in other words, remove from the indirect dependencies section the direct dependencies.

With [#185](https://github.com/EHDEN/NetworkDashboards/pull/185) we intend to start using the [pip-compile](https://github.com/jazzband/pip-tools) tool.
With it, we can have a file with the direct dependencies (requirements.in), and then pip-compile reads that file and automatically creates a requirements.txt file with all the dependencies and which package requires that specific dependency.
The update process of dependencies will then just be

1. Install the pip-compile tool `pip install pip-tools`
2. Make the change to the direct dependencies on the requirements.in file (No need for a virtual environment)
3. Call the pip-compile tool on the requirement.in file `pip-compile requirements.in`

### Documentation {-}
