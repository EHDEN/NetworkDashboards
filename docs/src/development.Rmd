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

Currently, we have made some modifications to the box plot visualization on our superset installation which doesn't allow us to use superset's pre-built images available on their docker hub, since we have to call npm's build procedures on the front-end code.
To build our custom docker image we used superset's [Dockerfile](https://github.com/apache/superset/blob/1.5.0/Dockerfile) as a base, where we removed the Dev section and added some code to install our chart plugins before building the front-end code.

The changes made to the Dockerfile to install the chart plugins are in [this](https://github.com/EHDEN/NetworkDashboards/blob/master/docker/superset/Dockerfile#L47-L49) area:

1. L46: Repalce some boxplot fiels with ours;
2. L47: Superset's original version of the controlPanel.ts file is a `.ts` versions however ours is a `.tsx`. For that, we have to remove the `.ts` version to properly override this file.

#### Update Superset {-}

1. `cd` into superset's submodule directory.

2. Get the latest tags: `git fetch -t`.

3. Checkout to the new desired release tag.

4. Check if there are any changes made to superset's Dockerfile (on the root of the repository for the current latest release), adapt them, and insert them on our custom Dockerfile under the `docker/superset` directory.

6. If the version of the plugin package `plugin-chart-echarts` changed, it's necessary to update our box plot plugin. If it is greater than 0.18.25, go to the history (`https://github.com/apache/superset/commits/[RELEASE-TAG]/superset-frontend/plugins/plugin-chart-echarts`) of commits done to the plugin-chart-echarts plugin update to the most recent commit, applying their changes to the files in the `superset/box-plot-overrides` directory. A fast way check the changes done between two commits: `git diff [old_commit_hash] [recent_commit_hash] -- superset-frontend/plugins/plugin-chart-echarts`

#### Chart Plugin Development {-}

1. Follow the instructions of [this tutorial](https://superset.apache.org/docs/contributing/creating-viz-plugins) to create the necessary base files of your plugin.

2. To deploy you can either use the `DYNAMIC_PLUGINS` feature flag or you can add and build your plugins in `superset/Dockerfile`.

#### Important features {-}

1. Standalone Mode: by appending `?standalone=true` to the URL of a dashboard superset's menu bar won't show.
   New versions support `?standalone=1` or `?standalone=2` where the first does the same as `?standalone=true` and the second also hides the bar containing the name of the dashboard, leaving just the charts.

2. Filters:
  - check [this](https://superset.apache.org/docs/frequently-asked-questions#how-to-add-dynamic-filters-to-a-dashboard) faq entry
  - Append `?preselect_filters={"chartId":{"columnToFilterBy":["value1", "value2"]}}` to the dashboard URL to apply a filter once the dashboard is loaded. E.g. `?preselect_filters={"13":{"name":["Demo University of Aveiro"]}}`

3. Custom label colors: check [this](https://superset.apache.org/docs/frequently-asked-questions#is-there-a-way-to-force-the-use-specific-colors) faq entry

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

To run only a single tool with tox you have to set the `TOX_ENV` enviroment variable. For example, to run just black with tox you can run `TOX_ENV=black tox`.

### Tests {-}

Our tests use Django's building testing features, which uses unittest under the hood.
Not all featured have tests associated, however, there are already [some tests scenarios](https://github.com/EHDEN/NetworkDashboards/issues?q=is%3Aissue+is%3Aopen+label%3A%22Test+Use+Case%22) in mind written as issues on the repository, which have the tag **Test Use Case**.

To run the tests we set up a docker-compose stack, under the [test](https://github.com/EHDEN/NetworkDashboards/tree/master/tests) directory which has just the necessary data containers (Redis and Postgres) with open ports and with no volumes, to avoid having to make changes on the development/production docker-compose stack to run the tests.
Once the stack is up it only necessary to run `python manage.py test` to execute the tests.
If you are developing any tests that involve [celery](https://github.com/celery/celery), there is no need to have a celery process running, since on Django's settings.py we [set the test runner](https://github.com/EHDEN/NetworkDashboards/blob/master/dashboard_viewer/dashboard_viewer/settings.py#L316) to the celery one.
This way the `python manage.py test` is enough to test the whole application.

tox is an alternative and a good way to run all test commands without having to install the test requirements for each test case (code style checks, unit tests, ...). tox will create a tox environment, install the necessary dependencies run the test command.

tox and its dependencies are in the file `requirements-dev/requirements-dev.txt`. After installing them you just need to execute `TOX_ENV=tests tox` or `TOX_ENV=tests-third-party tox` to run all the test cases.

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
A section on the GitBook is mapped to markdown headings elements of level 2 (H2 or ##).
This is, however, inconvenient for small chapters like the preface (index.Rmd).
To make it render all the sections on the same page, instead of using headings of level 2 (##) you should use level 3 (###).
Although this will make the section numeration start at 0, e.g 1.0.1, 1.0.2, ...
To avoid this we appended `{-}` to the sections titles so that the numeration does not show.

If a new file is created with more documentation, its name should be placed, including extension, in the desired location in [this list](https://github.com/EHDEN/NetworkDashboards/blob/master/docs/src/_bookdown.yml#L26-L45) of the `docks/src/_bookdown.yml` file.
