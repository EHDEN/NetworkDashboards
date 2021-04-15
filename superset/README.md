# Update Superset

1. `cd` into superset's submodule directory and checkout to the new desired release tag.

2. Check if there any changes made to superset's Dockerfile (on the root of the repository for the current latest release), adapt them, and insert them on our custom Dockerfile under the `docker/superset` directory.

3. Check if there any changes made to superset's `superset-frontend/src/visualizations/MainPreset.js` file. You can use the script `mainpreset_has_changes.py` under the `plugins` directory to check that. Apply the new changes if any and remember to keep our plugins imported and registered (Currently we only have the *Box plot* plugin).

4. If the version of the frontend package `@superset-ui/plugin-chart-echarts` changed it's necessary to update our box plot plugin. Follow the instructions present [here](https://github.com/EHDEN/NetworkDashboards/tree/master/superset/plugins/plugins/plugin-chart-box-plot#how-to-update) also take into account the instruction of the next section.

# Plugin Development

Instructions on how you can set up your development environment to develop on a custom superset plugin: and add it to develop a superset plugin:

1. Clone the [superset](https://github.com/apache/superset) repository. **IMPORTANT NOTE**: Since we build the superset's docker image using the existing superset's submodule, it's better not to use it to develop the plugins. If you decide to use it anyways, remember [this](https://github.com/EHDEN/NetworkDashboards/blob/master/docker/superset/Dockerfile#L54) and [this](https://github.com/EHDEN/NetworkDashboards/blob/master/docker/superset/Dockerfile#L99) steps. They might override directories (`superset-frontend/node_modules` and `superset/static/assets`) that are generated during the build process, which can cause frontend compilation errors or the app can serve outdated static files.

2. Clone the [superset-ui](https://github.com/apache-superset/superset-ui) repository into the directory superset-frontend of the superset repository.

1. Follow the instructions of [this tutorial](https://superset.apache.org/docs/installation/building-custom-viz-plugins) to create the necessary base files of your plugin.

2. Copy the file `MainPreset.js` present on this directory into the superset repository into the `superset-frontend/src/visualizations` directory.

3. Add the line `npm install --save ./superset-frontend/superset-ui/plugins/plugin-chart-[your-chart-name]` into the file `docker/docker-frontend.sh` of the superset repository before the existing `npm install ...` commands.

4. When the development is finished, on the root of the superset-ui repository run `yarn install` and then `yarn build [your-chart-name]`.

5. Copy the directory of your plugin (including its sub-directory `esm`), within the superset-ui repository within the directory `plugins`, into the sub-directory `plugins` this directory. Make sure to run the command `yarn build [your-chart-name]` before doing this step.
