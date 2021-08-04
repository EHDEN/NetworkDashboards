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

Currently, we have a custom chart plugin on our superset installation which doesn't allow us to use superset's pre-built images available on their docker hub, since we have to call npm's build procedures on the front-end code.
To build our custom docker image we used superset's [Dockerfile](https://github.com/apache/superset/blob/1.0.1/Dockerfile) as a base, where we removed the Dev section and added some code to install our chart plugins before building the front-end code.
Also, to make Superset import our custom chart plugins, some changes have to be made to the [superset-frontend/src/visualizations/presets/MainPreset.js](https://github.com/apache/superset/blob/1.0.1/superset-frontend/src/visualizations/presets/MainPreset.js) file.

The changes made to the Dockerfile to install the chart plugins are in [this](https://github.com/EHDEN/NetworkDashboards/blob/master/docker/superset/Dockerfile#L44-L63) area:

1. L44: First we copy the `superset/plugins` directory into the container, which contains all the extra and custom chart plugins.
2. L48-51: Then we iterate over the chart plugins and execute `npm install ...` on each of them.
   This will make changes to both the package.json and package-lock.json files and for that, we copy them into a temporary directory `package_json_files`.
3. L54: Then all superset's front-end code is copied into the container, which will override the package*.json files.
4. L56: After this, we copy our custom MainPresets.js file.
5. L60-L63: Finally, we replace the package*.json files with the ones that we saved earlier and then run the npm build command.

#### Update Superset {-}

1. Update repository's tags `git fetch --tags`.

2. `cd` into superset's submodule directory and checkout to the new desired release tag.

3. Check if there are any changes made to superset's Dockerfile (on the root of the repository for the current latest release), adapt them, and insert them on our custom Dockerfile under the `docker/superset` directory.

4. Check if there are any changes made to superset's `superset-frontend/src/visualizations/presets/MainPreset.js` file.
   You can use the script `mainpreset_has_changes.py` under the `plugins` directory to check that.
   Apply the new changes, if any, and remember to keep our chart plugins imported and registered (Currently we only have the *Box plot* plugin).

5. If the version of the frontend package `@superset-ui/plugin-chart-echarts` changed it's necessary to update our box plot plugin.
   Follow the instructions present [here](https://github.com/EHDEN/NetworkDashboards/tree/master/superset/plugins/plugins/plugin-chart-box-plot#how-to-update), also take into account the instruction of the next section.

#### Chart Plugin Development {-}

Instructions on how you can set up your development environment to develop a custom superset chart plugin:

1. Clone the [superset](https://github.com/apache/superset) repository.
   **IMPORTANT NOTE**: Since we build the superset's docker image using the existing superset's submodule, it's better not to use it to develop the plugins.
   If you decide to use it anyways, remember [this](https://github.com/EHDEN/NetworkDashboards/blob/master/docker/superset/Dockerfile#L54) and [this](https://github.com/EHDEN/NetworkDashboards/blob/master/docker/superset/Dockerfile#L99) steps.
   They might override directories (`superset-frontend/node_modules` and `superset/static/assets`) that are generated during the build process, which can cause frontend compilation errors or the app can serve outdated static files.

2. Clone the [superset-ui](https://github.com/apache-superset/superset-ui) repository into the directory superset-frontend of the superset's repository.

1. Follow the instructions of [this tutorial](https://superset.apache.org/docs/installation/building-custom-viz-plugins) to create the necessary base files of your plugin.

2. Copy the file `MainPreset.js` present on this directory into the superset repository into the `superset-frontend/src/visualizations/presets/` directory.

3. Add the line `npm install -f --no-optional --save ./superset-frontend/superset-ui/plugins/plugin-chart-[your-chart-name]` into the file `docker/docker-frontend.sh` of the superset repository before the existing `npm install ...` commands.

4. When the development is finished, on the root of the superset-ui repository run `yarn install` and then `yarn build [your-chart-name]`.

5. Copy the directory of your plugin (including its sub-directory `esm`), within the superset-ui repository within the directory `plugins`, into the sub-directory `plugins` this directory.
   Make sure to run the command `yarn build [your-chart-name]` before doing this step.

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

### Tests {-}

Our tests use Django's building testing features, which uses unittest under the hood.
Not all featured have tests associated, however, there are already [some tests scenarios](https://github.com/EHDEN/NetworkDashboards/issues?q=is%3Aissue+is%3Aopen+label%3A%22Test+Use+Case%22) in mind written as issues on the repository, which have the tag **Test Use Case**.

To run the tests we set up a docker-compose stack, under the [test](https://github.com/EHDEN/NetworkDashboards/tree/master/tests) directory which has just the necessary data containers (Redis and Postgres) to avoid having to make changes on the development/production docker-compose stack.
Once the stack is up it only necessary to run `SECRET_KEY=secret python manage.py test` to execute the tests.
If you are developing any tests that involve [celery](https://github.com/celery/celery), there is no need to have a celery process running, since on Django's settings.py we [set the test runner](https://github.com/EHDEN/NetworkDashboards/blob/master/dashboard_viewer/dashboard_viewer/settings.py#L316) to the celery one.
This way the `python manage.py test` is enough to test the whole application.

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
The `_build.sh` script executes three commands at the same time to generate different output formats which might conflict with eachother.
If some error happends telling that a file was not found and you didn't change nothing related to the specific file, rerun the `_build.sh` script.

In this documentation, we also describe all the settings around the dashboards that are used on the EHDEN project.
To avoid an extensive table of contents and also to avoid having a big chapter page for dashboards, we [configured](https://github.com/EHDEN/NetworkDashboards/blob/master/docs/src/_output.yml#L9) this GitBook to split different sections into different pages.
A section on the GitBook is mapped to markdown headings elements of level 2 (H2 or ##).
This is, however, inconvenient for small chapters like the preface (index.Rmd).
To make it render all the sections on the same page, instead of using headings of level 2 (##) you should use level 3 (###).
Although this will make the section numeration start at 0, e.g 1.0.1, 1.0.2, ...
To avoid this we appended `{-}` to the sections titles so that the numeration does not show.

If a new file is created with more documentation, its name should be placed, including extension, in the desired location in [this list](https://github.com/EHDEN/NetworkDashboards/blob/master/docs/src/_bookdown.yml#L26-L45) of the `docks/src/_bookdown.yml` file.
