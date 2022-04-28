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
import { LegendOrientation } from '../types';

import { getChartPadding } from '../utils/series';
import { TIMESERIES_CONSTANTS } from '../constants';

export function getPadding(
  showLegend: boolean,
  legendOrientation: LegendOrientation,
  addYAxisTitleOffset: boolean,
  zoomable: boolean,
  margin?: string | number | null,
  addXAxisTitleOffset?: boolean,
  yAxisTitlePosition?: string,
  yAxisTitleMargin?: number,
  xAxisTitleMargin?: number,
): {
  bottom: number;
  left: number;
  right: number;
  top: number;
} {
  const yAxisOffset = addYAxisTitleOffset ? TIMESERIES_CONSTANTS.yAxisLabelTopOffset : 0;
  const xAxisOffset = addXAxisTitleOffset ? xAxisTitleMargin || 0 : 0;
  return getChartPadding(showLegend, legendOrientation, margin, {
    top:
      yAxisTitlePosition && yAxisTitlePosition === 'Top'
        ? TIMESERIES_CONSTANTS.gridOffsetTop + (yAxisTitleMargin || 0)
        : TIMESERIES_CONSTANTS.gridOffsetTop + yAxisOffset,
    bottom: zoomable
      ? TIMESERIES_CONSTANTS.gridOffsetBottomZoomable + xAxisOffset
      : TIMESERIES_CONSTANTS.gridOffsetBottom + xAxisOffset,
    left:
      yAxisTitlePosition === 'Left'
        ? TIMESERIES_CONSTANTS.gridOffsetLeft + (yAxisTitleMargin || 0)
        : TIMESERIES_CONSTANTS.gridOffsetLeft,
    right:
      showLegend && legendOrientation === LegendOrientation.Right
        ? 0
        : TIMESERIES_CONSTANTS.gridOffsetRight,
  });
}
