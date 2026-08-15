export interface TurbineOption {
  label: string;
  value: string;
}

export interface TurbineProfile {
  turbineId: string;
  model: string;
  commissionDate: string;
  optimizationDate: string;
  analysisWindowDays: number;
}

export interface SummaryMetric {
  key: string;
  title: string;
  value: string;
  subtitle: string;
  trend: 'up' | 'down' | 'neutral';
  unit?: string;
  compactValue?: boolean;
}

export interface PowerCurvePoint {
  windSpeed: number;
  before: number;
  after: number;
}

export interface GenerationTrendPoint {
  month: string;
  baseline: number;
  optimized: number;
  upliftRate: number;
}

export interface GainByWindBinPoint {
  binLabel: string;
  gainRate: number;
}

export interface WindFrequencyPoint {
  windSpeed: number;
  frequencyRatio: number;
}

export interface RayleighParameters {
  sigma: number;
}

export interface RmsComparisonData {
  windows: string[];
  before: number[];
  after: number[];
  averageReduction: number;
}

export interface RampRateBin {
  label: string;
  before: number;
  after: number;
}

export interface TailRiskMetric {
  metric: 'Peak' | 'P95' | 'P99';
  before: number;
  after: number;
}

export interface VolatilityRmsWindow {
  window: '10s' | '60s' | '300s' | '600s';
  baseline: number;
  optimized: number;
  improvementPct: number;
}

export interface VolatilityRampBin {
  bin: '<-0.10' | '-0.10~-0.05' | '-0.05~0' | '0~0.05' | '0.05~0.10' | '>0.10';
  baselinePct: number;
  optimizedPct: number;
}

export interface VolatilityRampTailSummary {
  baselineExtremePct: number;
  optimizedExtremePct: number;
}

export interface VolatilityTailRiskPoint {
  baseline: number;
  optimized: number;
  improvementPct: number;
}

export interface VolatilityTailRisk {
  peak: VolatilityTailRiskPoint;
  p95: VolatilityTailRiskPoint;
  p99: VolatilityTailRiskPoint;
}

export interface VolatilityEventCoverage {
  validEventRatio: number;
  validEventCount: number;
  identifiedSampleCount: number;
  coveredWindBins: number;
  avgWindDelta: number;
  avgDuration: number;
}

export interface VolatilityResponseTimingSeries {
  start: number;
  peak: number;
  recovery: number;
}

export interface VolatilityResponseTiming {
  baseline: VolatilityResponseTimingSeries;
  optimized: VolatilityResponseTimingSeries;
  delta: VolatilityResponseTimingSeries;
}

export interface VolatilityInsightData {
  rmsWindows: VolatilityRmsWindow[];
  rampBins: VolatilityRampBin[];
  rampTailSummary: VolatilityRampTailSummary;
  tailRisk: VolatilityTailRisk;
  eventCoverage: VolatilityEventCoverage;
  responseTiming: VolatilityResponseTiming;
}

export type VolatilityMetricName = 'Peak' | 'P95' | 'P99';

export interface QuantileStats {
  p10: number;
  p25: number;
  median: number;
  p75: number;
  p90: number;
}

export interface DistributionShiftGroup {
  metric: VolatilityMetricName;
  baselineSamples: number[];
  optimizedSamples: number[];
  baselineStats: QuantileStats;
  optimizedStats: QuantileStats;
}

export interface DistributionShiftEvidence {
  metrics: VolatilityMetricName[];
  groups: DistributionShiftGroup[];
}

export interface TailCcdfEvidence {
  thresholds: number[];
  baselineCcdf: number[];
  optimizedCcdf: number[];
  baselineSamples: number[];
  optimizedSamples: number[];
  quantiles: {
    baseline: { p95: number; p99: number };
    optimized: { p95: number; p99: number };
  };
  markers: {
    baseline: {
      p95: { x: number; y: number; labelKey: 'baselineP95' };
      p99: { x: number; y: number; labelKey: 'baselineP99' };
    };
    optimized: {
      p95: { x: number; y: number; labelKey: 'optimizedP95' };
      p99: { x: number; y: number; labelKey: 'optimizedP99' };
    };
  };
}

export interface BootstrapMetricEvidence {
  metric: VolatilityMetricName;
  samples: number[];
  mean: number;
  median: number;
  ci95: [number, number];
}

export interface VolatilityEvidence {
  distributionShift: DistributionShiftEvidence;
  tailCcdf: TailCcdfEvidence;
  bootstrapStability: {
    metrics: BootstrapMetricEvidence[];
  };
}

export interface EventTemplatePoint {
  t: number;
  mean: number;
  lower: number;
  upper: number;
}

export interface ResponseSeriesPoint {
  t: number;
  value: number;
  lower: number;
  upper: number;
}

export interface EventMetricPoint {
  key: 'responseTime' | 'recoveryTime' | 'postEventRms';
  before: number;
  after: number;
}

export interface EventCoveragePoint {
  key: 'identifiedEventCount' | 'validEventCount' | 'coveredWindBins' | 'validEventRatio';
  value: number;
}

export type ResponseCoordinate = [number, number];

export interface AnnotationPoint {
  x: number;
  labelKey: 'responseStart' | 'rise10' | 'rise90' | 'peak' | 'settle';
}

export interface ResolvedAnnotationPoint {
  x: number;
  y: number;
  timeLabel: string;
}

export interface ResponseFeatureSet {
  responseStart: AnnotationPoint;
  rise10: AnnotationPoint;
  rise90: AnnotationPoint;
  peak: AnnotationPoint;
  settle: AnnotationPoint;
}

export interface ResponseSeriesData {
  baseline: ResponseCoordinate[];
  optimized: ResponseCoordinate[];
}

export interface ResponseFeatureMeta {
  x: number;
  y?: number;
  time: number;
  value?: number;
}

export interface ResponseFeatureMetaSet {
  responseStart: ResponseFeatureMeta;
  rise10: ResponseFeatureMeta;
  rise90: ResponseFeatureMeta;
  peak: ResponseFeatureMeta;
  settle: ResponseFeatureMeta;
}

export interface GustTemplateData {
  time: number[];
  mean: number[];
  upper: number[];
  lower: number[];
  annotation: GustTemplateAnnotation;
  activeWindow: GustActiveWindow;
}

export interface GustTemplateAnnotation {
  sampleCount: number;
  turbineCount: number;
  spanText: string;
  alignMethod: string;
  retentionRate: number;
  sampleIntervalText: string;
  infoLines: string[];
}

export interface GustActiveWindow {
  start: number;
  end: number;
  mid: number;
  label: string;
  source: 'derived_from_mean';
}

export interface ResponseKeyFeature {
  startTime: number;
  startValue: number;
  t10Time: number;
  t10Value: number;
  peakTime: number;
  peakValue: number;
  recoveryTime: number;
  recoveryValue: number;
}

export interface ResponseFeatureDelta {
  startLead: number;
  t10Lead: number;
  peakLead: number;
  peakGain: number;
  recoveryLead: number;
}

export interface ResponseComparisonFeatures {
  baseline: ResponseKeyFeature;
  optimized: ResponseKeyFeature;
  delta: ResponseFeatureDelta;
}

export interface GustResponseCardData {
  overview: GustResponseOverview;
  disturbanceTemplate: GustDisturbanceTemplate;
  powerResponse: GustPowerResponse;
  featureTimeline: GustFeatureTimeline;
  metricComparison: GustMetricComparisonRow[];
}

export interface GustResponseOverview {
  eventCount: number;
  turbineCount: number;
  alignSuccessRate: number;
  sampleRetentionRate: number;
  medianDuration: number;
  windowSec: number;
}

export interface GustDisturbanceTemplate {
  time: number[];
  mean: number[];
  lower: number[];
  upper: number[];
  disturbanceStart: number;
  disturbanceEnd: number;
  peakTime: number;
  peakValue: number;
}

export interface GustPowerResponse {
  time: number[];
  baseline: number[];
  optimized: number[];
  baselineBandLow: number[];
  baselineBandHigh: number[];
  optimizedBandLow: number[];
  optimizedBandHigh: number[];
}

export interface GustFeatureTimelineRow {
  responseStart: number;
  t10: number;
  peakTime: number;
  recoveryTime: number;
}

export interface GustFeatureTimeline {
  baseline: GustFeatureTimelineRow;
  optimized: GustFeatureTimelineRow;
}

export interface GustMetricComparisonRow {
  key: 'responseStart' | 't10' | 'peak' | 'peakTime' | 'recoveryTime' | 'rms';
  baseline: number;
  optimized: number;
  diff: number;
  unit: 's' | 'MW';
}
