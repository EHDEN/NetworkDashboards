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
import { buildQueryContext, getMetricLabel } from '@superset-ui/core';
const PERCENTILE_REGEX = /(\d+)\/(\d+) percentiles/;
export default function buildQuery(formData) {
  const {
    query_mode,
    whiskerOptions,
    columns: distributionColumns = []
  } = formData;
  return buildQueryContext(formData, baseQueryObject => {
    if (query_mode == 'raw') {
      const {
        groupby
      } = baseQueryObject;
      const {
        p10,
        p25,
        median,
        p75,
        p90
      } = formData;

      if (groupby.length == 0) {
        throw new Error(`Error: No series column defined.`);
      }

      const missing_columns = ['p10', 'p25', 'median', 'p75', 'p90'].filter(c => !formData[c] || Array.isArray(formData[c])).map(c => c.toUpperCase());

      if (missing_columns.length > 0) {
        if (missing_columns.length > 1) {
          throw new Error(`Error: Columns ${missing_columns.slice(0, missing_columns.length - 1).join(', ')} and ${missing_columns[missing_columns.length - 1]} are not defined.`);
        } else {
          throw new Error(`Error: Column ${missing_columns[0]} is not defined.`);
        }
      }

      const {
        outliers
      } = formData;
      const queries = [{ ...baseQueryObject,
        metrics: [],
        groupby: [],
        columns: [...groupby, p10, p25, median, p75, p90]
      }].concat(outliers && !Array.isArray(outliers) ? { ...baseQueryObject,
        metrics: [],
        groupby: [],
        columns: [...groupby, outliers]
      } : []);
      return queries;
    }

    let whiskerType;
    let percentiles;
    const {
      columns,
      metrics
    } = baseQueryObject;
    const percentileMatch = PERCENTILE_REGEX.exec(whiskerOptions);

    if (whiskerOptions === 'Tukey') {
      whiskerType = 'tukey';
    } else if (whiskerOptions === 'Min/max (no outliers)') {
      whiskerType = 'min/max';
    } else if (percentileMatch) {
      whiskerType = 'percentile';
      percentiles = [parseInt(percentileMatch[1], 10), parseInt(percentileMatch[2], 10)];
    } else {
      throw new Error(`Unsupported whisker type: ${whiskerOptions}`);
    }

    return [{ ...baseQueryObject,
      is_timeseries: distributionColumns.length === 0,
      post_processing: [{
        operation: 'boxplot',
        options: {
          whisker_type: whiskerType,
          percentiles,
          groupby: columns.filter(x => !distributionColumns.includes(x)),
          metrics: metrics.map(getMetricLabel)
        }
      }]
    }];
  });
}