/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import { CategoricalColorNamespace, getMetricLabel, getNumberFormatter } from '@superset-ui/core';
import { QueryMode } from './controlPanel';
import { extractGroupbyLabel } from '../utils/series';
import { defaultGrid, defaultTooltip, defaultYAxis } from '../defaults';
import d3 from 'd3';
export default function transformProps(chartProps) {
  const {
    width,
    height,
    formData,
    queriesData
  } = chartProps;
  const {
    colorScheme,
    queryMode,
    groupby = [],
    metrics: formdataMetrics = [],
    numberFormat,
    xTicksLayout
  } = formData;
  const colorFn = CategoricalColorNamespace.getScale(colorScheme);
  const numberFormatter = getNumberFormatter(numberFormat);
  let transformedData, outlierData;

  if (queryMode == QueryMode.raw) {
    const data = d3.nest().key(row => extractGroupbyLabel({
      datum: row,
      groupby
    })).entries(queriesData[0].data).reduce((result, item, _) => {
      result[item.key] = item.values[0];
      return result;
    }, {});
    const {
      outliers
    } = formData;
    let outlierMapping;

    if (outliers && !Array.isArray(outliers)) {
      outlierMapping = d3.nest().key(row => extractGroupbyLabel({
        datum: row,
        groupby
      })).entries(queriesData[1].data).reduce((result, item, _) => {
        const values = item.values.filter(v => v[outliers]);

        if (values.length > 0) {
          result[item.key] = values;
        }

        return result;
      }, {});
      outlierData = Object.entries(outlierMapping).map(([groupbyLabel, outlierDatum]) => {
        return {
          name: 'outlier',
          type: 'scatter',
          data: outlierDatum.map(val => [groupbyLabel, val[outliers]]),
          tooltip: {
            formatter: param => {
              const [outlierName, stats] = param.data;
              const headline = groupby ? `<p><strong>${outlierName}</strong></p>` : '';
              return `${headline}${numberFormatter(stats)}`;
            }
          },
          itemStyle: {
            color: colorFn(groupbyLabel)
          }
        };
      }).flat(2);
    }

    const {
      minimum,
      p10,
      p25,
      median,
      p75,
      p90,
      maximum
    } = formData;
    transformedData = Object.entries(data).map(([groupByLabel, datum]) => {
      return {
        name: groupByLabel,
        value: [datum[p10], datum[p25], datum[median], datum[p75], datum[p90], datum[minimum], datum[maximum], outlierMapping ? groupByLabel in outlierMapping ? outlierMapping[groupByLabel] : [] : []],
        itemStyle: {
          color: colorFn(groupByLabel),
          opacity: 0.6,
          borderColor: colorFn(groupByLabel)
        }
      };
    }).flatMap(row => row);
  } else {
    const data = queriesData[0].data || [];
    const metricLabels = formdataMetrics.map(getMetricLabel);
    transformedData = data.map(datum => {
      const groupbyLabel = extractGroupbyLabel({
        datum,
        groupby
      });
      return metricLabels.map(metric => {
        const name = metricLabels.length === 1 ? groupbyLabel : `${groupbyLabel}, ${metric}`;
        return {
          name,
          value: [datum[`${metric}__min`], datum[`${metric}__q1`], datum[`${metric}__median`], datum[`${metric}__q3`], datum[`${metric}__max`], datum[`${metric}__mean`], datum[`${metric}__count`], datum[`${metric}__outliers`]],
          itemStyle: {
            color: colorFn(groupbyLabel),
            opacity: 0.6,
            borderColor: colorFn(groupbyLabel)
          }
        };
      });
    }).flatMap(row => row);
    outlierData = data.map(datum => metricLabels.map(metric => {
      const groupbyLabel = extractGroupbyLabel({
        datum,
        groupby
      });
      const name = metricLabels.length === 1 ? groupbyLabel : `${groupbyLabel}, ${metric}`; // Outlier data is a nested array of numbers (uncommon, therefore no need to add to DataRecordValue)

      const outlierDatum = datum[`${metric}__outliers`] || [];
      return {
        name: 'outlier',
        type: 'scatter',
        data: outlierDatum.map(val => [name, val]),
        tooltip: {
          formatter: param => {
            const [outlierName, stats] = param.data;
            const headline = groupby ? `<p><strong>${outlierName}</strong></p>` : '';
            return `${headline}${numberFormatter(stats)}`;
          }
        },
        itemStyle: {
          color: colorFn(groupbyLabel)
        }
      };
    })).flat(2);
  }

  outlierData = outlierData || [];
  let axisLabel;
  if (xTicksLayout === '45°') axisLabel = {
    rotate: -45
  };else if (xTicksLayout === '90°') axisLabel = {
    rotate: -90
  };else if (xTicksLayout === 'flat') axisLabel = {
    rotate: 0
  };else if (xTicksLayout === 'staggered') axisLabel = {
    rotate: -45
  };else axisLabel = {
    show: true
  }; // @ts-ignore

  const echartOptions = {
    grid: { ...defaultGrid,
      top: 30,
      bottom: 30,
      left: 20,
      right: 20
    },
    xAxis: {
      type: 'category',
      data: transformedData.map(row => row.name),
      axisLabel
    },
    yAxis: { ...defaultYAxis,
      type: 'value',
      axisLabel: {
        formatter: numberFormatter
      }
    },
    tooltip: { ...defaultTooltip,
      trigger: 'item',
      axisPointer: {
        type: 'shadow'
      }
    },
    series: [{
      name: 'boxplot',
      type: 'boxplot',
      avoidLabelOverlap: true,
      // @ts-ignore
      data: transformedData,
      tooltip: {
        formatter: param => {
          // @ts-ignore
          const {
            value,
            name
          } = param;
          const headline = name ? `<p><strong>${name}</strong></p>` : '';
          let stats;

          if (queryMode == QueryMode.raw) {
            stats = [`Max: ${numberFormatter(value[7])}`, `90th Percentile: ${numberFormatter(value[5])}`, `75th Percentile: ${numberFormatter(value[4])}`, `Median: ${numberFormatter(value[3])}`, `25th Percentile: ${numberFormatter(value[2])}`, `10th Percentile: ${numberFormatter(value[1])}`, `Min: ${numberFormatter(value[6])}`];
          } else {
            stats = [`Max: ${numberFormatter(value[5])}`, `3rd Quartile: ${numberFormatter(value[4])}`, `Mean: ${numberFormatter(value[6])}`, `Median: ${numberFormatter(value[3])}`, `1st Quartile: ${numberFormatter(value[2])}`, `Min: ${numberFormatter(value[1])}`, `# Observations: ${numberFormatter(value[7])}`];
          }

          if (value[8].length > 0) {
            stats.push(`# Outliers: ${numberFormatter(value[8].length)}`);
          }

          return headline + stats.join('<br/>');
        }
      }
    }, // @ts-ignore
    ...outlierData]
  };
  return {
    width,
    height,
    echartOptions
  };
}