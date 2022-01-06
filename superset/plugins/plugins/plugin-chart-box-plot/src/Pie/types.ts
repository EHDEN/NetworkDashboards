import {
  QueryFormData,
} from '@superset-ui/core';
import {
  DEFAULT_LEGEND_FORM_DATA,
  EchartsLegendFormData,
  LegendOrientation,
  LegendType,
} from '../types';

export type EchartsPieFormData = QueryFormData &
  EchartsLegendFormData & {
    colorScheme?: string;
    currentOwnValue?: string[] | null;
    donut: boolean;
    defaultValue?: string[] | null;
    groupby: string[];
    innerRadius: number;
    labelLine: boolean;
    labelType: EchartsPieLabelType;
    labelsOutside: boolean;
    metric?: string;
    outerRadius: number;
    showLabels: boolean;
    numberFormat: string;
    dateFormat: string;
    showLabelsThreshold: number;
    emitFilter: boolean;
  };

export enum EchartsPieLabelType {
  Key = 'key',
  Value = 'value',
  Percent = 'percent',
  KeyValue = 'key_value',
  KeyPercent = 'key_percent',
  KeyValuePercent = 'key_value_percent',
}

// @ts-ignore
export const DEFAULT_FORM_DATA: EchartsPieFormData = {
    ...DEFAULT_LEGEND_FORM_DATA,
    donut: false,
    groupby: [],
    innerRadius: 30,
    labelLine: false,
    labelType: EchartsPieLabelType.Key,
    legendOrientation: LegendOrientation.Top,
    legendType: LegendType.Scroll,
    numberFormat: 'SMART_NUMBER',
    outerRadius: 70,
    showLabels: true,
    labelsOutside: true,
    showLabelsThreshold: 5,
    emitFilter: false,
    dateFormat: 'smart_date',
  };