import type {
  EventTemplatePoint,
  GainByWindBinPoint,
  PowerCurvePoint,
  RampRateBin,
  RmsComparisonData,
  ResponseSeriesData,
  ResponseSeriesPoint,
  TailRiskMetric,
  TurbineOption,
  TurbineProfile,
  RayleighParameters,
  WindFrequencyPoint,
} from '@/types/power-analysis';

export const turbineOptions: TurbineOption[] = [
  { label: 'WT-07', value: 'WT-07' },
  { label: 'WT-12', value: 'WT-12' },
  { label: 'WT-18', value: 'WT-18' },
];

export const turbineProfiles: TurbineProfile[] = [
  {
    turbineId: 'WT-07',
    model: 'B123-5MW',
    commissionDate: '2022-03-18',
    optimizationDate: '2024-07-01',
    analysisWindowDays: 180,
  },
  {
    turbineId: 'WT-12',
    model: 'B123-5MW',
    commissionDate: '2022-06-12',
    optimizationDate: '2024-07-01',
    analysisWindowDays: 180,
  },
  {
    turbineId: 'WT-18',
    model: 'B123-5MW',
    commissionDate: '2022-09-08',
    optimizationDate: '2024-07-01',
    analysisWindowDays: 180,
  },
];

export const powerCurveSeries: PowerCurvePoint[] = [
  { windSpeed: 3.0, before: 0.03, after: 0.03 },
  { windSpeed: 3.5, before: 0.08, after: 0.07 },
  { windSpeed: 4.0, before: 0.17, after: 0.16 },
  { windSpeed: 4.5, before: 0.29, after: 0.28 },
  { windSpeed: 5.0, before: 0.45, after: 0.46 },
  { windSpeed: 5.5, before: 0.66, after: 0.68 },
  { windSpeed: 6.0, before: 0.92, after: 0.95 },
  { windSpeed: 6.5, before: 1.23, after: 1.28 },
  { windSpeed: 7.0, before: 1.58, after: 1.65 },
  { windSpeed: 7.5, before: 1.95, after: 2.05 },
  { windSpeed: 8.0, before: 2.34, after: 2.47 },
  { windSpeed: 8.5, before: 2.72, after: 2.88 },
  { windSpeed: 9.0, before: 3.08, after: 3.26 },
  { windSpeed: 9.5, before: 3.43, after: 3.62 },
  { windSpeed: 10.0, before: 3.74, after: 3.92 },
  { windSpeed: 10.5, before: 4.01, after: 4.18 },
  { windSpeed: 11.0, before: 4.23, after: 4.38 },
  { windSpeed: 11.5, before: 4.4, after: 4.52 },
  { windSpeed: 12.0, before: 4.52, after: 4.61 },
  { windSpeed: 12.5, before: 4.6, after: 4.58 },
  { windSpeed: 13.0, before: 4.66, after: 4.64 },
  { windSpeed: 13.5, before: 4.71, after: 4.7 },
  { windSpeed: 14.0, before: 4.75, after: 4.74 },
  { windSpeed: 14.5, before: 4.78, after: 4.77 },
];

export const gainByWindBins: GainByWindBinPoint[] = [
  { binLabel: '3-4', gainRate: 0.2 },
  { binLabel: '4-5', gainRate: 0.5 },
  { binLabel: '5-6', gainRate: 0.9 },
  { binLabel: '6-7', gainRate: 1.4 },
  { binLabel: '7-8', gainRate: 2.1 },
  { binLabel: '8-9', gainRate: 2.8 },
  { binLabel: '9-10', gainRate: 3.1 },
  { binLabel: '10-11', gainRate: 2.7 },
  { binLabel: '11-12', gainRate: 2.0 },
  { binLabel: '12-13', gainRate: 1.3 },
  { binLabel: '13-14', gainRate: 0.8 },
  { binLabel: '14-15', gainRate: 0.4 },
];

export const windFrequencyRayleighParameters: RayleighParameters = {
  sigma: 9,
};

export const windFrequencyDistribution: WindFrequencyPoint[] = [];

export const rmsComparison: RmsComparisonData = {
  windows: ['10s', '30s', '60s', '120s', '300s', '600s'],
  before: [0.196, 0.178, 0.161, 0.145, 0.123, 0.108],
  after: [0.173, 0.155, 0.139, 0.126, 0.109, 0.096],
  averageReduction: 12.4,
};

export const rampRateDistribution: RampRateBin[] = [
  { label: '<-0.15', before: 5.0, after: 3.6 },
  { label: '-0.15~-0.10', before: 8.8, after: 7.4 },
  { label: '-0.10~-0.05', before: 14.6, after: 13.1 },
  { label: '-0.05~0', before: 20.8, after: 22.4 },
  { label: '0~0.05', before: 21.5, after: 23.7 },
  { label: '0.05~0.10', before: 15.2, after: 14.2 },
  { label: '0.10~0.15', before: 8.9, after: 7.8 },
  { label: '>0.15', before: 5.2, after: 4.0 },
];

export const tailRiskComparison: TailRiskMetric[] = [
  { metric: 'Peak', before: 4.88, after: 4.43 },
  { metric: 'P95', before: 4.31, after: 3.97 },
  { metric: 'P99', before: 4.62, after: 4.21 },
];

export const gustTemplateData = {
  mean: [
    [-20, 0.02], [-15, 0.06], [-10, 0.18], [-5, 0.42], [0, 0.95],
    [5, 1.45], [10, 1.82], [15, 1.70], [20, 1.35], [25, 0.92],
    [30, 0.55], [35, 0.28], [40, 0.12], [50, 0.03], [60, 0.0],
  ] as [number, number][],
  upper: [
    [-20, 0.12], [-15, 0.18], [-10, 0.34], [-5, 0.62], [0, 1.10],
    [5, 1.62], [10, 2.02], [15, 1.92], [20, 1.56], [25, 1.10],
    [30, 0.70], [35, 0.40], [40, 0.20], [50, 0.06], [60, 0.02],
  ] as [number, number][],
  lower: [
    [-20, -0.08], [-15, -0.04], [-10, 0.02], [-5, 0.20], [0, 0.78],
    [5, 1.28], [10, 1.62], [15, 1.50], [20, 1.16], [25, 0.74],
    [30, 0.40], [35, 0.18], [40, 0.04], [50, 0.0], [60, -0.02],
  ] as [number, number][],
};

export const eventTemplateSeries: EventTemplatePoint[] = gustTemplateData.mean.map(([t, mean], index) => ({
  t,
  mean,
  lower: gustTemplateData.lower[index][1],
  upper: gustTemplateData.upper[index][1],
}));

export const responseSeriesData: ResponseSeriesData = {
  baseline: [
    [-20, 2.78], [-15, 2.82], [-10, 2.88], [-5, 2.97], [0, 3.08],
    [5, 3.34], [10, 3.66], [15, 3.98], [20, 4.04], [25, 3.92],
    [30, 3.72], [35, 3.46], [40, 3.20], [45, 3.02], [50, 2.90],
    [55, 2.84], [60, 2.80],
  ],
  optimized: [
    [-20, 2.80], [-15, 2.84], [-10, 2.91], [-5, 3.03], [0, 3.20],
    [5, 3.52], [10, 3.86], [15, 4.14], [20, 4.16], [25, 4.02],
    [30, 3.82], [35, 3.54], [40, 3.27], [45, 3.08], [50, 2.94],
    [55, 2.86], [60, 2.82],
  ],
};

const responseSeriesBefore: ResponseSeriesPoint[] = responseSeriesData.baseline.map(([t, value]) => ({
  t,
  value,
  lower: value,
  upper: value,
}));

const responseSeriesAfter: ResponseSeriesPoint[] = responseSeriesData.optimized.map(([t, value]) => ({
  t,
  value,
  lower: value,
  upper: value,
}));
