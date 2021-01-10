## @superset-ui/plugin-chart-box-plot

Box Plot Chart with a raw mode. Based on the Box Plot present [here](https://github.com/apache-superset/superset-ui/tree/v0.16.5/plugins/plugin-chart-echarts)

[![Version](https://img.shields.io/npm/v/@superset-ui/plugin-chart-echarts.svg?style=flat-square)](https://www.npmjs.com/package/@superset-ui/plugin-chart-echarts)
[![David (path)](https://img.shields.io/david/apache-superset/superset-ui.svg?path=packages%2Fsuperset-ui-plugin-chart-echarts&style=flat-square)](https://david-dm.org/apache-superset/superset-ui?path=packages/superset-ui-plugin-chart-echarts)

This plugin provides Echarts viz plugins for Superset:

- Box Plot Chart

### Usage

Configure `key`, which can be any `string`, and register the plugin. This `key` will be used to
lookup this chart throughout the app.

```js
import {
  EchartsBoxPlotChartPlugin,
} from '@superset-ui/plugin-chart-box-plot';

new EchartsBoxPlotChartPlugin().configure({ key: 'box_plot' }).register();
```

Then use it via `SuperChart`. See
[storybook](https://apache-superset.github.io/superset-ui/?selectedKind=chart-plugins-plugin-chart-echarts)
for more details.

```js
<SuperChart
  chartType="echarts-ts"
  width={600}
  height={600}
  formData={...}
  queriesData={[{
    data: {...},
  }]}
/>
```
