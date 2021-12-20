# Development

Instructions on how you can set up your development environment to develop on a custom superset plugin: and add it to develop a superset plugin:

1. Clone the [superset](https://github.com/apache/superset) repository.

2. Clone the [superset-ui](https://github.com/apache-superset/superset-ui) repository into the directory superset-frontend of the superset repository.

1. Follow the instructions of [this tutorial](https://superset.apache.org/docs/installation/building-custom-viz-plugins) to create the necessary base files of your plugin.

2. Copy the file `MainPreset.js` present on this directory into the superset repository into the `superset-frontend/src/visualizations` directory.

3. Add the line `npm install --save ./superset-frontend/superset-ui/plugins/plugin-chart-[your-chart-name]` into the file `docker/docker-frontend.sh` of the superset repository before the existing `npm install ...` commands.

4. When the development is finished, on the root of the superset-ui repository run `yarn install` and then `yarn build [your-chart-name]`.

5. Copy the directory of your plugin (including its sub-directory `esm`), within the superset-ui repository within the directory `plugins`, into the sub-directory `plugins` this directory. Make sure to run the command `yarn build [your-chart-name]` before doing this step.
