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
import { buildQueryContext } from '@superset-ui/core';
import { boxplotOperator } from '@superset-ui/chart-controls';
import { BoxPlotQueryFormData } from './types';

export default function buildQuery(formData: BoxPlotQueryFormData) {
  const {
    query_mode,
    minimum,
    p10,
    p25,
    median,
    p75,
    p90,
    maximum,
    columns = [],
    granularity_sqla,
    groupby = [],
  } = formData;
  return buildQueryContext(formData, baseQueryObject => {
    if (query_mode === 'raw') {
      if (groupby.length === 0) {
        throw new Error(`Error: No series column defined.`);
      }

      const missing_columns = [
        'minimum',
        'p10',
        'p25',
        'median',
        'p75',
        'p90',
        'maximum',
      ]
        .filter(c => !formData[c] || Array.isArray(formData[c]))
        .map(c => c.toUpperCase());
      if (missing_columns.length > 0) {
        if (missing_columns.length > 1) {
          throw new Error(
            `Error: Columns ${missing_columns
              .slice(0, missing_columns.length - 1)
              .join(', ')} and ${
              missing_columns[missing_columns.length - 1]
            } are not defined.`,
          );
        } else {
          throw new Error(
            `Error: Column ${missing_columns[0]} is not defined.`,
          );
        }
      }

      const { outliers } = formData;

      const queries = [
        {
          ...baseQueryObject,
          metrics: [],
          series_columns: groupby,
          columns: [...groupby, minimum, p10, p25, median, p75, p90, maximum],
        },
      ].concat(
        outliers && !Array.isArray(outliers)
          ? {
              ...baseQueryObject,
              metrics: [],
              series_columns: groupby,
              columns: [...groupby, outliers],
            }
          : [],
      );

      return queries;
    }

    const distributionColumns: string[] = [];
    // For now default to using the temporal column as distribution column.
    // In the future this control should be made mandatory.
    if (!columns.length && granularity_sqla) {
      distributionColumns.push(granularity_sqla);
    }
    return [
      {
        ...baseQueryObject,
        columns: [...distributionColumns, ...columns, ...groupby],
        series_columns: groupby,
        post_processing: [boxplotOperator(formData, baseQueryObject)],
      },
    ];
  });
}
