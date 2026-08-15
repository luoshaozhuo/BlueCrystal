import type {
  BootstrapMetricEvidence,
  DistributionShiftGroup,
  GainByWindBinPoint,
  GustActiveWindow,
  GustResponseCardData,
  GustTemplateAnnotation,
  GustTemplateData,
  PowerCurvePoint,
  QuantileStats,
  RayleighParameters,
  ResponseComparisonFeatures,
  ResponseKeyFeature,
  TurbineOption,
  TurbineProfile,
  VolatilityEvidence,
  VolatilityMetricName,
} from '@/types/power-analysis';
import {
  turbineOptions,
  turbineProfiles,
  windFrequencyRayleighParameters,
} from './fixtures';

function round(value: number, digits = 3) {
  return Number(value.toFixed(digits));
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function createTimeAxis(step = 2, end = 40) {
  return Array.from({ length: end / step + 1 }, (_, index) => index * step);
}

function createSigmoid(x: number) {
  return 1 / (1 + Math.exp(-x));
}

function createSmoothStep(t: number, start: number, end: number) {
  if (t <= start) return 0;
  if (t >= end) return 1;
  const x = (t - start) / (end - start);
  return x * x * (3 - 2 * x);
}

function smoothSeries(series: number[]) {
  return series.map((value, index, arr) => {
    const prev = arr[Math.max(index - 1, 0)];
    const next = arr[Math.min(index + 1, arr.length - 1)];
    return round((prev + value * 2 + next) / 4);
  });
}

function randomNormal(mean: number, stdDev: number) {
  const u = Math.max(Math.random(), 1e-6);
  const v = Math.max(Math.random(), 1e-6);
  const z = Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  return mean + z * stdDev;
}

function sortAscending(values: number[]) {
  return [...values].sort((a, b) => a - b);
}

function computePercentile(sortedValues: number[], percentile: number) {
  if (!sortedValues.length) return 0;
  const position = (sortedValues.length - 1) * percentile;
  const lowerIndex = Math.floor(position);
  const upperIndex = Math.ceil(position);
  const lower = sortedValues[lowerIndex] ?? sortedValues[sortedValues.length - 1];
  const upper = sortedValues[upperIndex] ?? sortedValues[sortedValues.length - 1];
  const weight = position - lowerIndex;
  return round(lower + (upper - lower) * weight, 3);
}

function computeQuantiles(values: number[]): QuantileStats {
  const sorted = sortAscending(values);
  return {
    p10: computePercentile(sorted, 0.1),
    p25: computePercentile(sorted, 0.25),
    median: computePercentile(sorted, 0.5),
    p75: computePercentile(sorted, 0.75),
    p90: computePercentile(sorted, 0.9),
  };
}

function computeMean(values: number[]) {
  return values.reduce((sum, value) => sum + value, 0) / Math.max(values.length, 1);
}

function resample(values: number[]) {
  return Array.from(
    { length: values.length },
    () => values[randomInteger(0, values.length - 1)] ?? values[0] ?? 0,
  );
}

function createTailRiskSampleSet(metric: VolatilityMetricName) {
  const size = randomInteger(32, 38);
  const config = {
    Peak: { baselineMean: 4.84, optimizedMean: 4.33, baselineStd: 0.28, optimizedStd: 0.20, tailWeight: 0.24 },
    P95: { baselineMean: 4.26, optimizedMean: 3.93, baselineStd: 0.18, optimizedStd: 0.14, tailWeight: 0.16 },
    P99: { baselineMean: 4.58, optimizedMean: 4.12, baselineStd: 0.22, optimizedStd: 0.17, tailWeight: 0.20 },
  }[metric];

  const buildSamples = (mean: number, stdDev: number, tailWeight: number, shiftBias: number) =>
    sortAscending(
      Array.from({ length: size }, (_, index) => {
        const base = randomNormal(mean, stdDev);
        const tailBoost =
          index > size * (1 - tailWeight)
            ? randomFloat(0.08 + shiftBias, 0.28 + shiftBias, 3)
            : 0;
        return round(Math.max(base + tailBoost, 3.2), 3);
      }),
    );

  return {
    baselineSamples: buildSamples(config.baselineMean, config.baselineStd, config.tailWeight, 0.04),
    optimizedSamples: buildSamples(config.optimizedMean, config.optimizedStd, config.tailWeight * 0.72, 0),
  };
}

function buildDistributionShiftEvidence() {
  const metrics: VolatilityMetricName[] = ['Peak', 'P95', 'P99'];
  const groups: DistributionShiftGroup[] = metrics.map((metric) => {
    const { baselineSamples, optimizedSamples } = createTailRiskSampleSet(metric);
    return {
      metric,
      baselineSamples,
      optimizedSamples,
      baselineStats: computeQuantiles(baselineSamples),
      optimizedStats: computeQuantiles(optimizedSamples),
    };
  });

  return {
    metrics,
    groups,
  };
}

function buildCcdfEvidence(groups: DistributionShiftGroup[]) {
  const baselineSamples = groups.flatMap((group) => group.baselineSamples);
  const optimizedSamples = groups.flatMap((group) => group.optimizedSamples);
  const combined = [...baselineSamples, ...optimizedSamples];
  const minValue = Math.min(...combined);
  const maxValue = Math.max(...combined);
  const thresholdCount = 24;
  const step = (maxValue - minValue) / (thresholdCount - 1);
  const thresholds = Array.from({ length: thresholdCount }, (_, index) => round(minValue + step * index, 3));

  const computeCcdf = (samples: number[]) =>
    thresholds.map((threshold) => round(samples.filter((value) => value > threshold).length / samples.length, 4));

  function interpolateCcdfY(ccdfThresholds: number[], ccdf: number[], x: number) {
    if (x <= ccdfThresholds[0]) return ccdf[0];
    if (x >= ccdfThresholds[ccdfThresholds.length - 1]) return ccdf[ccdf.length - 1];

    for (let index = 0; index < ccdfThresholds.length - 1; index += 1) {
      const x0 = ccdfThresholds[index];
      const x1 = ccdfThresholds[index + 1];
      if (x >= x0 && x <= x1) {
        const y0 = ccdf[index];
        const y1 = ccdf[index + 1];
        const ratio = (x - x0) / Math.max(x1 - x0, 1e-6);
        return round(y0 + (y1 - y0) * ratio, 4);
      }
    }

    return ccdf[ccdf.length - 1];
  }

  const baselineCcdf = computeCcdf(baselineSamples);
  const optimizedCcdf = computeCcdf(optimizedSamples);
  const baselineP95 = computePercentile(sortAscending(baselineSamples), 0.95);
  const baselineP99 = computePercentile(sortAscending(baselineSamples), 0.99);
  const optimizedP95 = computePercentile(sortAscending(optimizedSamples), 0.95);
  const optimizedP99 = computePercentile(sortAscending(optimizedSamples), 0.99);

  return {
    thresholds,
    baselineCcdf,
    optimizedCcdf,
    baselineSamples,
    optimizedSamples,
    quantiles: {
      baseline: {
        p95: baselineP95,
        p99: baselineP99,
      },
      optimized: {
        p95: optimizedP95,
        p99: optimizedP99,
      },
    },
    markers: {
      baseline: {
        p95: { x: baselineP95, y: interpolateCcdfY(thresholds, baselineCcdf, baselineP95), labelKey: 'baselineP95' as const },
        p99: { x: baselineP99, y: interpolateCcdfY(thresholds, baselineCcdf, baselineP99), labelKey: 'baselineP99' as const },
      },
      optimized: {
        p95: { x: optimizedP95, y: interpolateCcdfY(thresholds, optimizedCcdf, optimizedP95), labelKey: 'optimizedP95' as const },
        p99: { x: optimizedP99, y: interpolateCcdfY(thresholds, optimizedCcdf, optimizedP99), labelKey: 'optimizedP99' as const },
      },
    },
  };
}

function buildBootstrapEvidence(groups: DistributionShiftGroup[]) {
  const metrics: BootstrapMetricEvidence[] = groups.map((group) => {
    const samples = Array.from({ length: 100 }, () => {
      const baselineResample = resample(group.baselineSamples);
      const optimizedResample = resample(group.optimizedSamples);
      const baselineStat = computeMean(baselineResample);
      const optimizedStat = computeMean(optimizedResample);
      return round(((baselineStat - optimizedStat) / baselineStat) * 100, 3);
    });
    const sorted = sortAscending(samples);

    return {
      metric: group.metric,
      samples,
      mean: round(computeMean(samples), 3),
      median: computePercentile(sorted, 0.5),
      ci95: [computePercentile(sorted, 0.025), computePercentile(sorted, 0.975)],
    };
  });

  return { metrics };
}

function createVolatilityEvidenceMock(): VolatilityEvidence {
  const distributionShift = buildDistributionShiftEvidence();

  return {
    distributionShift,
    tailCcdf: buildCcdfEvidence(distributionShift.groups),
    bootstrapStability: buildBootstrapEvidence(distributionShift.groups),
  };
}

const daysWindow = 180;

const gustMeta = {
  detectedEventCount: 141.5,
  validEventCount: 117,
  alignedEventCount: 106.9,
};

function calcRetentionRate(valid: number, detected: number) {
  return Number(((valid / detected) * 100).toFixed(1));
}

function calcAlignmentSuccessRate(aligned: number, valid: number) {
  return Number(((aligned / valid) * 100).toFixed(1));
}

const windBins = [
  { ws: 3.0, gainMw: -0.02 },
  { ws: 3.5, gainMw: -0.015 },
  { ws: 4.0, gainMw: 0.01 },
  { ws: 4.5, gainMw: 0.015 },
  { ws: 5.0, gainMw: 0.02 },
  { ws: 5.5, gainMw: -0.005 },
  { ws: 6.0, gainMw: 0.03 },
  { ws: 6.5, gainMw: -0.005 },
  { ws: 7.0, gainMw: -0.01 },
  { ws: 7.5, gainMw: 0.14 },
  { ws: 8.0, gainMw: 0.18 },
  { ws: 8.5, gainMw: 0.21 },
  { ws: 9.0, gainMw: 0.23 },
  { ws: 9.5, gainMw: 0.22 },
  { ws: 10.0, gainMw: 0.2 },
  { ws: 10.5, gainMw: 0.17 },
  { ws: 11.0, gainMw: -0.01 },
  { ws: 11.5, gainMw: 0.02 },
  { ws: 12.0, gainMw: 0.01 },
];

function calcPositiveGainBinRate(bins: Array<{ ws: number; gainMw: number }>) {
  const positive = bins.filter((item) => item.gainMw > 0).length;
  return Number(((positive / bins.length) * 100).toFixed(1));
}

function calcMainContributionBand(bins: Array<{ ws: number; gainMw: number }>) {
  const positiveBins = bins.filter((item) => item.gainMw > 0);
  let bestStart = 0;
  let bestEnd = 0;
  let bestSum = -Infinity;

  for (let index = 0; index < positiveBins.length; index += 1) {
    let sum = 0;
    for (let cursor = index; cursor < positiveBins.length; cursor += 1) {
      const prev = cursor > index ? positiveBins[cursor - 1].ws : positiveBins[index].ws;
      const current = positiveBins[cursor].ws;
      if (cursor > index && Math.abs(current - prev) > 0.51) break;
      sum += positiveBins[cursor].gainMw;
      if (sum > bestSum) {
        bestSum = sum;
        bestStart = index;
        bestEnd = cursor;
      }
    }
  }

  return {
    start: positiveBins[bestStart].ws,
    end: positiveBins[bestEnd].ws,
    text: `${positiveBins[bestStart].ws.toFixed(1)}–${positiveBins[bestEnd].ws.toFixed(1)}`,
  };
}

const derivedMetrics = {
  retentionRate: calcRetentionRate(gustMeta.validEventCount, gustMeta.detectedEventCount),
  alignmentSuccessRate: calcAlignmentSuccessRate(gustMeta.alignedEventCount, gustMeta.validEventCount),
  positiveGainBinRate: calcPositiveGainBinRate(windBins),
  mainContributionBand: calcMainContributionBand(windBins),
};

const baselinePowerCurveMap = new Map([
  [3.0, 0.03],
  [3.5, 0.08],
  [4.0, 0.17],
  [4.5, 0.29],
  [5.0, 0.45],
  [5.5, 0.66],
  [6.0, 0.92],
  [6.5, 1.23],
  [7.0, 1.58],
  [7.5, 1.95],
  [8.0, 2.34],
  [8.5, 2.72],
  [9.0, 3.08],
  [9.5, 3.43],
  [10.0, 3.74],
  [10.5, 4.01],
  [11.0, 4.23],
  [11.5, 4.4],
  [12.0, 4.52],
]);

export const gainByWindBins: GainByWindBinPoint[] = windBins.map((item, index, list) => {
  const nextWindSpeed = list[index + 1]?.ws;
  const upperBound = nextWindSpeed ?? item.ws + 0.5;
  return {
    binLabel: `${item.ws.toFixed(1)}-${upperBound.toFixed(1)}`,
    gainRate: round(item.gainMw, 3),
  };
});

export const powerCurveSeries: PowerCurvePoint[] = windBins.map((item) => {
  const before = baselinePowerCurveMap.get(item.ws) ?? 0;
  return {
    windSpeed: item.ws,
    before,
    after: round(before + item.gainMw, 2),
  };
});

export const summaryMetrics = [
  {
    key: 'netAepGain',
    value: '2.8%',
    trend: 'up',
  },
  {
    key: 'avgPowerGain',
    value: '1.7%',
    trend: 'up',
  },
  {
    key: 'rmsReduction',
    value: '12.4%',
    trend: 'down',
  },
  {
    key: 'tailRiskReduction',
    value: '9.6%',
    trend: 'down',
  },
  {
    key: 'validEventCount',
    value: `${gustMeta.validEventCount}`,
    trend: 'neutral',
  },
  {
    key: 'retentionRate',
    value: `${derivedMetrics.retentionRate.toFixed(1)}%`,
    trend: 'neutral',
  },
  {
    key: 'alignmentSuccessRate',
    value: `${derivedMetrics.alignmentSuccessRate.toFixed(1)}%`,
    trend: 'neutral',
  },
  {
    key: 'mainContributionBand',
    value: derivedMetrics.mainContributionBand.text,
    unit: 'm/s',
    compactValue: true,
    trend: 'neutral',
  },
  {
    key: 'positiveGainBinRate',
    value: `${derivedMetrics.positiveGainBinRate.toFixed(1)}%`,
    trend: 'neutral',
  },
] satisfies Array<{
  key: string;
  value: string;
  trend: 'up' | 'down' | 'neutral';
  unit?: string;
  compactValue?: boolean;
}>;

function interpolateSeriesValue(time: number[], series: number[], targetTime: number) {
  if (targetTime <= time[0]) return series[0];
  if (targetTime >= time[time.length - 1]) return series[series.length - 1];

  for (let index = 1; index < time.length; index += 1) {
    if (targetTime <= time[index]) {
      const t0 = time[index - 1];
      const t1 = time[index];
      const v0 = series[index - 1];
      const v1 = series[index];
      const ratio = (targetTime - t0) / Math.max(t1 - t0, 1e-6);
      return round(v0 + (v1 - v0) * ratio, 3);
    }
  }

  return series[series.length - 1];
}

function findPeakIndex(series: number[]) {
  return series.reduce(
    (bestIndex, value, index, arr) => (value > arr[bestIndex] ? index : bestIndex),
    0,
  );
}

function hasSustainedDelta(delta: number[], threshold: number, index: number, consecutiveCount: number) {
  return Array.from({ length: consecutiveCount }, (_, offset) => delta[index + offset] >= threshold).every(Boolean);
}

function hasSustainedDecay(delta: number[], threshold: number, slope: number[], index: number, consecutiveCount: number) {
  return Array.from(
    { length: consecutiveCount },
    (_, offset) => delta[index + offset] <= threshold && slope[index + offset] <= 0,
  ).every(Boolean);
}

export function createGustTemplateAnnotationMock(): GustTemplateAnnotation {
  const sampleCount = gustMeta.validEventCount;
  const turbineCount = 9;
  const retentionRate = derivedMetrics.retentionRate;
  const sampleInterval = 1;
  const alignMethod = '阵风起点对齐';

  return {
    sampleCount,
    turbineCount,
    spanText: `近${daysWindow}天`,
    alignMethod,
    retentionRate,
    sampleIntervalText: `${sampleInterval} s`,
    infoLines: [
      `有效事件数：${sampleCount}`,
      `覆盖机组数：${turbineCount} 台`,
      `时间跨度：近${daysWindow}天`,
      `对齐方式：${alignMethod}`,
      `样本保留率：${retentionRate.toFixed(1)}%`,
      `采样周期：${sampleInterval} s`,
    ],
  };
}

export function createGustActiveWindowMock(time: number[], mean: number[]): GustActiveWindow {
  const baselineCount = Math.max(3, Math.floor(mean.length * 0.14));
  const baselineWindow = mean.slice(0, baselineCount);
  const baseline = baselineWindow.reduce((sum, value) => sum + value, 0) / Math.max(baselineWindow.length, 1);
  const peakIndex = findPeakIndex(mean);
  const peakValue = mean[peakIndex] ?? 0;
  const peakDelta = peakValue - baseline;
  const slope = mean.map((value, index) => (index === 0 ? 0 : value - mean[index - 1]));
  const delta = mean.map((value) => value - baseline);
  const riseThreshold = peakDelta * 0.18;
  const settleThreshold = peakDelta * 0.22;
  const sustainedPoints = 2;
  const minStartIndex = Math.max(2, Math.floor(time.length * 0.18));
  const maxEndIndex = Math.min(time.length - 1, peakIndex + Math.max(4, Math.floor(time.length * 0.26)));

  let startCandidate = minStartIndex;
  for (let index = minStartIndex; index <= Math.max(minStartIndex, peakIndex - sustainedPoints); index += 1) {
    const rising = Array.from({ length: sustainedPoints }, (_, offset) => slope[index + offset] > 0).every(Boolean);
    if (rising && hasSustainedDelta(delta, riseThreshold, index, sustainedPoints)) {
      startCandidate = index;
      break;
    }
  }
  startCandidate = Math.max(minStartIndex, startCandidate);

  let endCandidate = maxEndIndex;
  let foundDecay = false;
  for (let index = peakIndex + 1; index <= maxEndIndex - sustainedPoints + 1; index += 1) {
    if (hasSustainedDecay(delta, settleThreshold, slope, index, sustainedPoints)) {
      endCandidate = index;
      foundDecay = true;
      break;
    }
  }
  if (!foundDecay) {
    for (let index = maxEndIndex - sustainedPoints + 1; index >= Math.max(peakIndex + 1, startCandidate + 1); index -= 1) {
      if (hasSustainedDelta(delta, riseThreshold, index, sustainedPoints)) {
        endCandidate = Math.min(maxEndIndex, index + sustainedPoints - 1);
        break;
      }
    }
  }

  const startIndex = clamp(startCandidate, minStartIndex, maxEndIndex - 1);
  const endIndex = clamp(endCandidate, startIndex + 1, maxEndIndex);

  return {
    start: time[startIndex] ?? time[0] ?? 0,
    end: time[endIndex] ?? time[time.length - 1] ?? 0,
    mid: ((time[startIndex] ?? 0) + (time[endIndex] ?? 0)) / 2,
    label: '阵风作用区间',
    source: 'derived_from_mean',
  };
}

export function createGustTemplateMock(): GustTemplateData {
  const time = createTimeAxis();
  const baselineLevel = randomFloat(0.02, 0.05, 2);
  const amplitude = randomFloat(1.42, 1.58, 2);
  const plateauBump = randomFloat(0.08, 0.16, 2);

  const mean = time.map((t) => {
    const rise = createSmoothStep(t, 6, 14);
    const fall = createSmoothStep(t, 22, 30);
    const plateau = rise * (1 - fall);
    const tailRecovery = createSmoothStep(t, 30, 40);
    const plateauShape = plateau * (1 + plateauBump * Math.exp(-((t - 18) ** 2) / 18));
    const value = baselineLevel + amplitude * plateauShape * (1 - 0.05 * tailRecovery);
    const relaxed = baselineLevel + (value - baselineLevel) * (1 - 0.9 * tailRecovery);
    return round(relaxed);
  });

  const spread = time.map((t) => {
    const mid = 0.055 + 0.11 * Math.exp(-((t - 18) ** 2) / 60);
    const shoulder = 0.015 * Math.exp(-((t - 10) ** 2) / 25);
    return round(mid + shoulder);
  });
  const upper = mean.map((value, index) => round(value + Math.max(spread[index] * 3, 0.06)));
  const lower = mean.map((value, index) => round(value - Math.max(spread[index] * 3, 0.06)));

  const annotation = createGustTemplateAnnotationMock();
  const activeWindow = createGustActiveWindowMock(time, mean);

  return {
    time,
    mean,
    upper,
    lower,
    annotation,
    activeWindow,
  };
}

function findSustainedIndex(values: number[], predicate: (value: number) => boolean, count = 2, startIndex = 0) {
  for (let index = startIndex; index <= values.length - count; index += 1) {
    if (Array.from({ length: count }, (_, offset) => predicate(values[index + offset])).every(Boolean)) {
      return index;
    }
  }
  return -1;
}

function createResponseFeatures(time: number[], series: number[]): ResponseKeyFeature {
  const baselineCount = Math.max(2, Math.floor(time.length * 0.15));
  const baselineValue =
    series.slice(0, baselineCount).reduce((sum, value) => sum + value, 0) / Math.max(baselineCount, 1);
  const peakIndex = findPeakIndex(series);
  const peakValue = series[peakIndex] ?? baselineValue;
  const peakDelta = peakValue - baselineValue;
  const threshold10 = baselineValue + peakDelta * 0.1;
  const deltaSeries = series.map((value) => value - baselineValue);
  const settleThreshold = peakDelta * 0.1;

  const startIndexRaw = findSustainedIndex(series, (value) => value >= threshold10, 2, 0);
  const startIndex = startIndexRaw >= 0 ? startIndexRaw : Math.max(0, peakIndex - 2);
  const t10Index = startIndex;

  const recoverySearch = deltaSeries.slice(peakIndex + 1);
  const recoveryOffset = findSustainedIndex(recoverySearch, (value) => value <= settleThreshold, 2, 0);
  const recoveryIndex =
    recoveryOffset >= 0 ? peakIndex + 1 + recoveryOffset : Math.max(peakIndex + 1, time.length - 2);

  return {
    startTime: round(time[startIndex] ?? time[0] ?? 0, 1),
    startValue: round(series[startIndex] ?? baselineValue, 2),
    t10Time: round(time[t10Index] ?? time[0] ?? 0, 1),
    t10Value: round(series[t10Index] ?? baselineValue, 2),
    peakTime: round(time[peakIndex] ?? time[0] ?? 0, 1),
    peakValue: round(peakValue, 2),
    recoveryTime: round(time[recoveryIndex] ?? time[time.length - 1] ?? 0, 1),
    recoveryValue: round(series[recoveryIndex] ?? series[series.length - 1] ?? baselineValue, 2),
  };
}

function formatSigned(value: number, digits: number, unit: string) {
  const rounded = Number(value.toFixed(digits));
  if (rounded === 0) return `0.0${unit}`;
  return `${rounded > 0 ? '+' : ''}${rounded.toFixed(digits)}${unit}`;
}

function randomInteger(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomFloat(min: number, max: number, digits: number) {
  const value = min + Math.random() * (max - min);
  return Number(value.toFixed(digits));
}

function createResponseComparisonFeatures(
  baselineTime: number[],
  baseline: number[],
  optimizedTime: number[],
  optimized: number[],
): ResponseComparisonFeatures {
  const baselineFeatures = createResponseFeatures(baselineTime, baseline);
  const optimizedFeatures = createResponseFeatures(optimizedTime, optimized);
  const delta = {
    startLead: round(optimizedFeatures.startTime - baselineFeatures.startTime, 1),
    t10Lead: round(optimizedFeatures.t10Time - baselineFeatures.t10Time, 1),
    peakLead: round(optimizedFeatures.peakTime - baselineFeatures.peakTime, 1),
    peakGain: round(optimizedFeatures.peakValue - baselineFeatures.peakValue, 2),
    recoveryLead: round(optimizedFeatures.recoveryTime - baselineFeatures.recoveryTime, 1),
  };

  return {
    baseline: baselineFeatures,
    optimized: optimizedFeatures,
    delta,
  };
}

export function createGustResponseCardMock(): GustResponseCardData {
  return {
    overview: {
      eventCount: 117,
      turbineCount: 9,
      alignSuccessRate: 91.4,
      sampleRetentionRate: 82.7,
      medianDuration: 18.0,
      windowSec: 40,
    },
    disturbanceTemplate: {
      time: [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40],
      mean: [0.02, 0.03, 0.03, 0.05, 0.12, 0.35, 0.72, 1.15, 1.48, 1.62, 1.55, 1.36, 1.08, 0.76, 0.38, 0.14, 0.06, 0.03, 0.02, 0.02, 0.02],
      lower: [0.0, 0.01, 0.01, 0.02, 0.06, 0.2, 0.46, 0.82, 1.1, 1.22, 1.18, 1.04, 0.82, 0.56, 0.24, 0.08, 0.03, 0.01, 0.0, 0.0, 0.0],
      upper: [0.05, 0.06, 0.06, 0.09, 0.2, 0.52, 0.98, 1.46, 1.82, 2.0, 1.92, 1.7, 1.38, 1.02, 0.56, 0.24, 0.1, 0.05, 0.04, 0.04, 0.04],
      disturbanceStart: 8,
      disturbanceEnd: 28,
      peakTime: 18,
      peakValue: 1.62,
    },
    powerResponse: {
      time: [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40],
      baseline: [2.7, 2.7, 2.7, 2.72, 2.78, 2.9, 3.05, 3.22, 3.36, 3.5, 3.46, 3.3, 3.12, 2.88, 2.62, 2.42, 2.28, 2.2, 2.16, 2.12, 2.1],
      optimized: [3.3, 3.3, 3.3, 3.32, 3.4, 3.58, 3.84, 4.1, 4.36, 4.66, 4.6, 4.36, 4.02, 3.62, 3.24, 2.92, 2.74, 2.62, 2.56, 2.5, 2.46],
      baselineBandLow: [2.62, 2.62, 2.62, 2.64, 2.7, 2.82, 2.96, 3.12, 3.26, 3.4, 3.36, 3.2, 3.02, 2.78, 2.54, 2.34, 2.2, 2.12, 2.08, 2.04, 2.02],
      baselineBandHigh: [2.78, 2.78, 2.78, 2.8, 2.86, 2.98, 3.14, 3.32, 3.46, 3.6, 3.56, 3.4, 3.22, 2.98, 2.7, 2.5, 2.36, 2.28, 2.24, 2.2, 2.18],
      optimizedBandLow: [3.22, 3.22, 3.22, 3.24, 3.32, 3.48, 3.72, 3.96, 4.2, 4.5, 4.44, 4.22, 3.88, 3.5, 3.14, 2.84, 2.66, 2.54, 2.48, 2.42, 2.38],
      optimizedBandHigh: [3.38, 3.38, 3.38, 3.4, 3.48, 3.68, 3.96, 4.24, 4.52, 4.82, 4.76, 4.5, 4.16, 3.74, 3.34, 3.0, 2.82, 2.7, 2.64, 2.58, 2.54],
    },
    featureTimeline: {
      baseline: {
        responseStart: 8.6,
        t10: 13.6,
        peakTime: 18.6,
        recoveryTime: 28.6,
      },
      optimized: {
        responseStart: 8.0,
        t10: 13.0,
        peakTime: 18.0,
        recoveryTime: 28.0,
      },
    },
    metricComparison: [
      { key: 'responseStart', baseline: 8.6, optimized: 8.0, diff: -0.6, unit: 's' },
      { key: 't10', baseline: 13.6, optimized: 13.0, diff: -0.6, unit: 's' },
      { key: 'peak', baseline: 3.5, optimized: 4.66, diff: 1.16, unit: 'MW' },
      { key: 'peakTime', baseline: 18.6, optimized: 18.0, diff: -0.6, unit: 's' },
      { key: 'recoveryTime', baseline: 28.6, optimized: 28.0, diff: -0.6, unit: 's' },
      { key: 'rms', baseline: 0.41, optimized: 0.36, diff: -0.05, unit: 'MW' },
    ],
  };
}

export const gustResponseCardData = createGustResponseCardMock();

export const volatilityEvidence = createVolatilityEvidenceMock();

export {
  turbineOptions,
  turbineProfiles,
  windFrequencyRayleighParameters,
};

export type {
  GainByWindBinPoint,
  PowerCurvePoint,
  RayleighParameters,
  TurbineOption,
  TurbineProfile,
};
