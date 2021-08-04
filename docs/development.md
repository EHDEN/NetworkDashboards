# Development Instructions

### Repository Structure Description {-}

- **backups**: Scripts and configuration files to perform backups of all the data involved in the Network Dashboards applications (Dashboard viewer + Superset)

- **dashboard_viewer**: The Dashboard Viewer Django application to manage and upload catalogue results data. More detail can be found in the [Code Documentation](code-documentation.html) chapter.

- **demo**: Files that can be used to test some processes of the platform (Upload catalogue results data and import a simple dashboard)

- **docker**: Docker-compose stack-related directories.
  - Environment file
  - Configuration directories (Nginx and Postgres)
  - Custom Superest Dockerfile <!-- TODO link to the subsection on the Superset section -->

  For more information about docker deployment consult the [Installation](installation.html) chapter.

- **docs**: Where the files of this gitbook are hosted. Other output formats can also be obtained here. Consult the [Documentation](development-instructions.html#documentation) section of this chapter for more details.

- **superset**: contains a submodule to the latest supported version  of Superset's repository and our custom chart plugins

- **tests**: contains files to launch a docker-compose stack specific to run tests.

- **requirements-dev**: python requirements files to the several tools to either perform code style checks or to run Django tests

- **.pre-commit-config.yaml**: configuration for the [pre-commit](https://pre-commit.com/) tool. This is not mandatory to use but is a good tool to automatically fix problems related to code style on staged files

- **setup.cfg**: configurations for the several code style tools

- **tox.ini**: configuration for the [tox](https://tox.readthedocs.io/) tool. It helps automate the process to check if the code style is correct and if the Django tests are passing

  It's extremely useful in this context since different code style check tools that we use have some conflicts with python dependencies. It creates a virtual environment for each tox environment, in our case, for each code style check tool plus Django tests

### Superset {-}

### Github Actions {-}

Github has a feature that allows performing automatic actions after a certain event happens on the repository.
We use this feature to execute to check if everything is alright with new PR before merging them to dev.

Github calls a job a set of steps that are executed after a certain event.
Then several jobs can be groups in workflows.
Events are defined at the workflow level, so all the jobs in a workflow will execute at the same time.

We have two workflows:

1. Code analysis checks
2. Django tests

The first has three jobs

1. [black](https://github.com/psf/black): ensures that python's code format is consistent throughout the project
2. [isort](https://github.com/PyCQA/isort): sorts and organizes import statements
3. [prospector](https://github.com/PyCQA/prospector): executes a set of tools that perform some code analysis

The second has just one job that executes the Django tests.

Both workflows execute on commits of pull requests that will be merged into the dev branch.

Regarding the code analysis workflow, the three tools used have requirements that conflict with each other, for that there is a requirements file for each tool on the `requirement-dev` directory of the repository.
To avoid having three different virtual environments for each tool, you can use the [tox](https://tox.readthedocs.io/).
You just need to install the development requirements (`pip install -r requirements-dev/requirements-dev.txt`) and then just run `tox`.
It will manage the necessary virtual environments and install the requirements for each tool.
If you, however, want to run a specific tool manually you can check the tox configuration file ([tox.ini](https://github.com/EHDEN/NetworkDashboards/blob/master/tox.ini)).
For example for the prospector tool the tox configuration is the following:
```
[testenv:prospector]
basepython = python3.8
deps =
    -r{toxinidir}/requirements-dev/requirements-prospector.txt
    -r{toxinidir}/dashboard_viewer/requirements.txt
commands =
    prospector dashboard_viewer
    prospector docker/superset
```
we can see that it installs the requirement for the prospector tool and also the requirements of the Dashboard Viewer Django app and then runs two commands.

For both black and isort tools, when you run tox, it will show the necessary changes that are required to make the code good.
You can apply the changes automatically by executing the tools manually without the `--check` and `--check-only` options respectively.

Sometimes prospector can be a pain in the boot, complaining about too much stuff.
You can make prospector ignore some bad stuff by adding the comment, ` # noqa`, to the end of the specific line where it is complaining.

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

The plan is to have all the documentation on this git book and any other places that might require some description/information should point to this GitBook so we maintain a commonplace for all the documentation.
This way we can make sure that the code and the documentation are in the same place since on a pull request for a specific feature or a bug fix, associated documentation should also be changed with it.

The manual was written in [RMarkdown](https://rmarkdown.rstudio.com) using the [bookdown](https://bookdown.org) package.
All the code is stored in the `docs/src` directory as well as the script to build all the documentation.
**Do not change** the files in the root of the `docs` directory, because those files will be removed during the build processed and replaced by the new ones.
Therefore, to update this documentation, apply the changes to the files in the directory `docs/src`.
To build the documentation, you need to have [R](https://www.r-project.org/) installed, and if you are using UNIX-based systems, you only need to run `sh _build.sh` in the `docs/src` directory.

In this documentation, we also describe all the settings around the dashboards that are used on the EHDEN project.
To avoid an extensive table of contents and also to avoid having a big chapter page for dashboards, we [configured](https://github.com/EHDEN/NetworkDashboards/blob/master/docs/src/_output.yml#L9) this GitBook to split different sections into different pages.
A section on the GitBook is mapped to markdown headings elements of level 1 (H1 or #).
This is, however, inconvenient for small chapters like the preface (index.Rmd).
To make it render all the sections on the same page, instead of using headings of level 1 (#) you should use level 2 (##).
Although this will make the section numeration start at 0, e.g 1.0.1, 1.0.2, ...
To avoid this we appended `{-}` to the sections titles so that the numeration does not show.

If a new file is created with more documentation, its name should be placed, including extension, in the desired location in [this list](https://github.com/EHDEN/NetworkDashboards/blob/master/docs/src/_bookdown.yml#L26-L45) of the `docks/src/_bookdown.yml` file.
