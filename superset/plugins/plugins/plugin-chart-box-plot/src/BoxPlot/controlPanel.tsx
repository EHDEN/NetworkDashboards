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
import React from 'react';
import {
  FeatureFlag,
  isFeatureEnabled,
  QueryFormColumn,
  QueryMode,
  t,
} from '@superset-ui/core';
  
import {
  ColumnOption,
  ControlConfig,
  ControlStateMapping,
  ControlPanelsContainerProps,
  D3_FORMAT_DOCS,
  D3_FORMAT_OPTIONS,
  D3_TIME_FORMAT_OPTIONS,
  formatSelectOptions,
  sections,
  sharedControls,
  QueryModeLabel,
} from '@superset-ui/chart-controls';
import { DEFAULT_FORM_DATA } from '../Pie/types';

const { emitFilter } = DEFAULT_FORM_DATA;

function getQueryMode(controls: ControlStateMapping): QueryMode {
  const mode = controls?.query_mode?.value;
  if (mode === QueryMode.aggregate || mode === QueryMode.raw) {
    return mode as QueryMode;
  }
  const rawColumns = controls?.all_columns?.value as QueryFormColumn[] | undefined;
  const hasRawColumns = rawColumns && rawColumns.length > 0;
  return hasRawColumns ? QueryMode.raw : QueryMode.aggregate;
}

/**
 * Visibility check
 */
function isQueryMode(mode: QueryMode) {
  return ({ controls }: ControlPanelsContainerProps) => getQueryMode(controls) === mode;
}

const isAggMode = isQueryMode(QueryMode.aggregate);
const isRawMode = isQueryMode(QueryMode.raw);

const queryMode: ControlConfig<'RadioButtonControl'> = {
  type: 'RadioButtonControl',
  label: t('Query mode'),
  default: null,
  options: [
    [QueryMode.aggregate, QueryModeLabel[QueryMode.aggregate]],
    [QueryMode.raw, QueryModeLabel[QueryMode.raw]]
  ],
  mapStateToProps: ({ controls }) => ({ value: getQueryMode(controls) }),
};

const all_columns: typeof sharedControls.groupby = {
  type: 'SelectControl',
  label: t('P90'),
  description: t('Column holding the 90th percentile values'),
  multi: false,
  freeForm: false,
  allowAll: true,
  commaChoosesOption: false,
  default: [],
  optionRenderer: c => <ColumnOption showType column={c} />,
  valueRenderer: c => <ColumnOption column={c} />,
  valueKey: 'column_name',
  mapStateToProps: ({ datasource, controls }) => ({
    options: datasource?.columns || [],
    queryMode: getQueryMode(controls),
  }),
  visibility: isRawMode,
};


export default {
  controlPanelSections: [
    sections.legacyTimeseriesTime,
    {
      label: t('Query'),
      expanded: true,
      controlSetRows: [
        [
          {
            name: 'query_mode',
            config: queryMode,
          },
        ],
        [
          {
            name: 'minimum',
            config: {
              ...all_columns,
              label: t('Min'),
              description: t('Column holding the minimum values'),
            },
          },
        ],
        [
          {
            name: 'p10',
            config: {
              ...all_columns,
              label: t('P10'),
              description: t('Column holding the 10th percentile values'),
            },
          },
          {
            name: 'p25',
            config: {
              ...all_columns,
              label: t('P25'),
              description: t('Column holding the 25th percentile values'),
            },
          },
        ],
        [
          {
            name: 'median',
            config: {
              ...all_columns,
              label: t('Median/P50'),
              description: t('Column holding the median values'),
            },
          },
        ],
        [
          {
            name: 'p75',
            config: {
              ...all_columns,
              label: t('P75'),
              description: t('Column holding the 75th percentile values'),
            },
          },
          {
            name: 'p90',
            config: all_columns,
          },
        ],
        [
          {
            name: 'maximum',
            config: {
              ...all_columns,
              label: t('Max'),
              description: t('Column holding the maximum values'),
            },
          },
        ],
        [
          {
            name: 'outliers',
            config: {
              ...all_columns,
              label: t('Outliers'),
              description: t('Column holding outliers values'),
            },
          },
        ],
        ['metrics'],
        ['adhoc_filters'],
        ['groupby'],
        ['columns'],
        ['limit'],
        [
          {
            name: 'whiskerOptions',
            config: {
              type: 'SelectControl',
              freeForm: true,
              label: t('Whisker/outlier options'),
              default: 'Tukey',
              description: t('Determines how whiskers and outliers are calculated.'),
              choices: formatSelectOptions([
                'Tukey',
                'Min/max (no outliers)',
                '2/98 percentiles',
                '9/91 percentiles',
              ]),
              visibility: isAggMode,
            },
          },
        ],
      ],
    },
    {
      label: t('Chart Options'),
      expanded: true,
      controlSetRows: [
        ['color_scheme'],
        isFeatureEnabled(FeatureFlag.DASHBOARD_CROSS_FILTERS)
          ? [
              {
                name: 'emit_filter',
                config: {
                  type: 'CheckboxControl',
                  label: t('Enable emitting filters'),
                  default: emitFilter,
                  renderTrigger: true,
                  description: t('Enable emmiting filters.'),
                },
              },
            ]
          : [],
        [
          {
            name: 'x_ticks_layout',
            config: {
              type: 'SelectControl',
              label: t('X Tick Layout'),
              choices: formatSelectOptions(['auto', 'flat', '45°', '90°', 'staggered']),
              default: 'auto',
              clearable: false,
              renderTrigger: true,
              description: t('The way the ticks are laid out on the X-axis'),
            },
          },
        ],
        [
          {
            name: 'number_format',
            config: {
              type: 'SelectControl',
              freeForm: true,
              label: t('Number format'),
              renderTrigger: true,
              default: 'SMART_NUMBER',
              choices: D3_FORMAT_OPTIONS,
              description: `${t('D3 format syntax: https://github.com/d3/d3-format')} ${t(
                'Only applies when "Label Type" is set to show values.',
              )}`,
            },
          },
        ],
        [
          {
            name: 'date_format',
            config: {
              type: 'SelectControl',
              freeForm: true,
              label: t('Date format'),
              renderTrigger: true,
              choices: D3_TIME_FORMAT_OPTIONS,
              default: 'smart_date',
              description: D3_FORMAT_DOCS,
            },
          },
        ],
      ],
    },
  ],
  controlOverrides: {
    groupby: {
      label: t('Series'),
      description: t('Categories to group by on the x-axis.'),
      multi: true,
    },
    columns: {
      label: t('Distribute across'),
      multi: true,
      description: t(
        'Columns to calculate distribution across. Defaults to temporal column if left empty.',
      ),
      visibility: isAggMode,
    },
    metrics: {
      visibility: isAggMode,
      validators: [],
    },
  },
};
