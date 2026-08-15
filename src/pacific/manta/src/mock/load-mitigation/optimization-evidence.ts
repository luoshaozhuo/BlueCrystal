export interface EvidenceMetricSource {
  metricKey: string;
  baselineMatrix: number[][];
  optimizedMatrix: number[][];
  rmsWindowLabels?: string[];
  energySpectrum?: EnergySpectrumPoint[];
  beforePeaks?: number[];
  afterPeaks?: number[];
  measurementUnit?: string;
  measurementBase?: number;
  measurementScale?: number;
  measurementSpread?: number;
  baselineDamage?: number[];
  optimizedDamage?: number[];
  baselineShock?: number[];
  optimizedShock?: number[];
}

export interface EvidenceBarDatum {
  label: string;
  baseline: number;
  optimized: number;
  changePct: number;
}

export interface PeakQqEvidence {
  beforePeaks: number[];
  afterPeaks: number[];
}

export interface EvidenceStabilityDatum {
  key: 'rmsDropWindowRatio' | 'p95DropWindowRatio' | 'peakDropWindowRatio';
  value: number;
}

export interface EnergySpectrumPoint {
  frequency: number;
  before: number;
  after: number;
}

export interface OptimizationEvidence {
  unit: string;
  rmsSeries: EvidenceBarDatum[];
  peakQqEvidence: PeakQqEvidence;
  stabilitySeries: EvidenceStabilityDatum[];
  energySpectrum: EnergySpectrumPoint[];
}

const defaultPeakQqEvidenceMap: Record<string, PeakQqEvidence> = {
  blade_root_moment: {
    beforePeaks: [
      30.62, 30.91, 31.18, 31.47, 31.73, 31.95, 32.22, 32.48, 32.76, 32.98,
      33.21, 33.55, 33.78, 34.02, 34.31, 34.58, 34.85, 35.12, 35.41, 35.67,
      35.95, 36.24, 36.58, 36.87, 37.11, 37.44, 37.69, 37.95, 38.22, 38.58,
      38.91, 39.28, 39.55, 39.92, 40.18, 40.54, 40.89, 41.17, 41.55, 41.88,
      42.16, 42.48, 42.81, 43.12, 43.45, 43.79, 44.06, 44.41, 44.75, 45.13,
      45.49, 45.86, 46.18, 46.55, 46.92, 47.36,
    ],
    afterPeaks: [
      28.94, 29.18, 29.46, 29.71, 29.97, 30.18, 30.49, 30.72, 30.94, 31.17,
      31.42, 31.73, 31.95, 32.18, 32.44, 32.76, 33.01, 33.28, 33.55, 33.81,
      34.06, 34.29, 34.58, 34.82, 35.07, 35.29, 35.56, 35.84, 36.12, 36.37,
      36.63, 36.91, 37.18, 37.42, 37.78, 38.06, 38.31, 38.68, 38.94, 39.21,
      39.48, 39.75, 40.09, 40.38, 40.64, 40.89, 41.12, 41.38, 41.67, 41.93,
      42.19, 42.47, 42.82, 43.06, 43.33, 43.67,
    ],
  },
  nacelle_acceleration: {
    beforePeaks: [
      0.214, 0.219, 0.223, 0.228, 0.231, 0.235, 0.239, 0.243, 0.247, 0.252,
      0.257, 0.261, 0.266, 0.271, 0.275, 0.279, 0.284, 0.289, 0.295, 0.301,
      0.306, 0.311, 0.317, 0.322, 0.329, 0.334, 0.341, 0.347, 0.353, 0.359,
      0.366, 0.372, 0.379, 0.386, 0.393, 0.399, 0.407, 0.414, 0.421, 0.428,
      0.437, 0.445, 0.453, 0.462, 0.471, 0.479, 0.488, 0.497,
    ],
    afterPeaks: [
      0.201, 0.205, 0.209, 0.214, 0.217, 0.221, 0.225, 0.229, 0.233, 0.238,
      0.243, 0.248, 0.252, 0.256, 0.261, 0.265, 0.271, 0.276, 0.281, 0.287,
      0.292, 0.298, 0.304, 0.309, 0.316, 0.321, 0.327, 0.334, 0.341, 0.347,
      0.353, 0.36, 0.367, 0.374, 0.38, 0.388, 0.395, 0.402, 0.409, 0.417,
      0.425, 0.433, 0.441, 0.45, 0.458, 0.466, 0.475, 0.484,
    ],
  },
  generator_torque: {
    beforePeaks: [
      18.62, 18.94, 19.23, 19.58, 19.86, 20.17, 20.44, 20.78, 21.06, 21.34,
      21.68, 21.95, 22.28, 22.57, 22.89, 23.18, 23.47, 23.81, 24.15, 24.43,
      24.79, 25.08, 25.41, 25.77, 26.08, 26.42, 26.79, 27.11, 27.48, 27.83,
      28.15, 28.52, 28.91, 29.24, 29.63, 30.02, 30.38, 30.71, 31.08, 31.46,
      31.88, 32.24, 32.61, 33.03, 33.46, 33.88, 34.31, 34.76, 35.18, 35.67,
    ],
    afterPeaks: [
      17.81, 18.07, 18.34, 18.63, 18.92, 19.18, 19.46, 19.78, 20.05, 20.31,
      20.62, 20.88, 21.14, 21.43, 21.75, 22.01, 22.29, 22.56, 22.88, 23.13,
      23.47, 23.76, 24.08, 24.37, 24.68, 24.97, 25.31, 25.64, 25.95, 26.27,
      26.61, 26.94, 27.28, 27.63, 27.94, 28.31, 28.66, 29.02, 29.37, 29.74,
      30.1, 30.46, 30.84, 31.21, 31.58, 31.97, 32.38, 32.77, 33.15, 33.58,
    ],
  },
};

const defaultEnergySpectrumEvidenceMap: Record<string, EnergySpectrumPoint[]> = {
  blade_root_moment: [
    { frequency: 0.5, before: 0.21, after: 0.2 },
    { frequency: 1.2, before: 0.24, after: 0.22 },
    { frequency: 1.9, before: 0.3, after: 0.27 },
    { frequency: 2.6, before: 0.39, after: 0.34 },
    { frequency: 3.3, before: 0.47, after: 0.41 },
    { frequency: 4, before: 0.56, after: 0.47 },
    { frequency: 4.7, before: 0.68, after: 0.55 },
    { frequency: 5.4, before: 0.82, after: 0.65 },
    { frequency: 6.1, before: 0.94, after: 0.74 },
    { frequency: 6.8, before: 1.04, after: 0.82 },
    { frequency: 7.5, before: 1.12, after: 0.88 },
    { frequency: 8.2, before: 1.17, after: 0.91 },
    { frequency: 8.9, before: 1.2, after: 0.92 },
    { frequency: 9.6, before: 1.16, after: 0.89 },
    { frequency: 10.3, before: 1.08, after: 0.84 },
    { frequency: 11, before: 0.98, after: 0.77 },
    { frequency: 11.7, before: 0.87, after: 0.72 },
    { frequency: 12.4, before: 0.78, after: 0.66 },
    { frequency: 13.1, before: 0.7, after: 0.61 },
    { frequency: 13.8, before: 0.64, after: 0.58 },
    { frequency: 14.5, before: 0.58, after: 0.54 },
    { frequency: 15.2, before: 0.52, after: 0.5 },
    { frequency: 15.9, before: 0.47, after: 0.46 },
    { frequency: 16.6, before: 0.44, after: 0.43 },
    { frequency: 17.3, before: 0.41, after: 0.42 },
    { frequency: 18, before: 0.39, after: 0.4 },
    { frequency: 18.7, before: 0.37, after: 0.39 },
    { frequency: 19.4, before: 0.36, after: 0.36 },
    { frequency: 20.1, before: 0.33, after: 0.34 },
    { frequency: 20.8, before: 0.3, after: 0.31 },
    { frequency: 21.5, before: 0.28, after: 0.29 },
    { frequency: 22.2, before: 0.27, after: 0.27 },
    { frequency: 22.9, before: 0.25, after: 0.26 },
    { frequency: 23.6, before: 0.24, after: 0.24 },
    { frequency: 24.3, before: 0.22, after: 0.23 },
    { frequency: 25, before: 0.21, after: 0.21 },
    { frequency: 25.7, before: 0.19, after: 0.2 },
    { frequency: 26.4, before: 0.18, after: 0.18 },
    { frequency: 27.1, before: 0.16, after: 0.17 },
    { frequency: 27.8, before: 0.15, after: 0.16 },
    { frequency: 28.5, before: 0.14, after: 0.14 },
    { frequency: 29.2, before: 0.13, after: 0.13 },
  ],
  nacelle_acceleration: [
    { frequency: 0.5, before: 0.18, after: 0.18 },
    { frequency: 1.2, before: 0.22, after: 0.2 },
    { frequency: 1.9, before: 0.28, after: 0.25 },
    { frequency: 2.6, before: 0.35, after: 0.31 },
    { frequency: 3.3, before: 0.43, after: 0.37 },
    { frequency: 4, before: 0.52, after: 0.43 },
    { frequency: 4.7, before: 0.63, after: 0.5 },
    { frequency: 5.4, before: 0.76, after: 0.59 },
    { frequency: 6.1, before: 0.92, after: 0.69 },
    { frequency: 6.8, before: 1.05, after: 0.78 },
    { frequency: 7.5, before: 1.15, after: 0.84 },
    { frequency: 8.2, before: 1.22, after: 0.88 },
    { frequency: 8.9, before: 1.26, after: 0.9 },
    { frequency: 9.6, before: 1.21, after: 0.88 },
    { frequency: 10.3, before: 1.12, after: 0.82 },
    { frequency: 11, before: 1.02, after: 0.75 },
    { frequency: 11.7, before: 0.93, after: 0.7 },
    { frequency: 12.4, before: 0.84, after: 0.65 },
    { frequency: 13.1, before: 0.76, after: 0.61 },
    { frequency: 13.8, before: 0.69, after: 0.58 },
    { frequency: 14.5, before: 0.63, after: 0.55 },
    { frequency: 15.2, before: 0.57, after: 0.52 },
    { frequency: 15.9, before: 0.52, after: 0.49 },
    { frequency: 16.6, before: 0.48, after: 0.47 },
    { frequency: 17.3, before: 0.45, after: 0.45 },
    { frequency: 18, before: 0.43, after: 0.44 },
    { frequency: 18.7, before: 0.41, after: 0.42 },
    { frequency: 19.4, before: 0.39, after: 0.4 },
    { frequency: 20.1, before: 0.36, after: 0.37 },
    { frequency: 20.8, before: 0.33, after: 0.35 },
    { frequency: 21.5, before: 0.31, after: 0.32 },
    { frequency: 22.2, before: 0.29, after: 0.3 },
    { frequency: 22.9, before: 0.27, after: 0.28 },
    { frequency: 23.6, before: 0.25, after: 0.26 },
    { frequency: 24.3, before: 0.23, after: 0.24 },
    { frequency: 25, before: 0.22, after: 0.22 },
    { frequency: 25.7, before: 0.2, after: 0.21 },
    { frequency: 26.4, before: 0.19, after: 0.19 },
    { frequency: 27.1, before: 0.18, after: 0.18 },
    { frequency: 27.8, before: 0.16, after: 0.17 },
    { frequency: 28.5, before: 0.15, after: 0.16 },
    { frequency: 29.2, before: 0.14, after: 0.14 },
  ],
  generator_torque: [
    { frequency: 0.5, before: 0.19, after: 0.18 },
    { frequency: 1.2, before: 0.22, after: 0.2 },
    { frequency: 1.9, before: 0.27, after: 0.24 },
    { frequency: 2.6, before: 0.34, after: 0.3 },
    { frequency: 3.3, before: 0.41, after: 0.36 },
    { frequency: 4, before: 0.49, after: 0.41 },
    { frequency: 4.7, before: 0.58, after: 0.48 },
    { frequency: 5.4, before: 0.69, after: 0.56 },
    { frequency: 6.1, before: 0.82, after: 0.66 },
    { frequency: 6.8, before: 0.95, after: 0.75 },
    { frequency: 7.5, before: 1.06, after: 0.82 },
    { frequency: 8.2, before: 1.13, after: 0.87 },
    { frequency: 8.9, before: 1.16, after: 0.89 },
    { frequency: 9.6, before: 1.12, after: 0.86 },
    { frequency: 10.3, before: 1.04, after: 0.8 },
    { frequency: 11, before: 0.95, after: 0.74 },
    { frequency: 11.7, before: 0.87, after: 0.69 },
    { frequency: 12.4, before: 0.79, after: 0.64 },
    { frequency: 13.1, before: 0.72, after: 0.6 },
    { frequency: 13.8, before: 0.66, after: 0.57 },
    { frequency: 14.5, before: 0.61, after: 0.54 },
    { frequency: 15.2, before: 0.56, after: 0.51 },
    { frequency: 15.9, before: 0.51, after: 0.49 },
    { frequency: 16.6, before: 0.47, after: 0.46 },
    { frequency: 17.3, before: 0.44, after: 0.44 },
    { frequency: 18, before: 0.42, after: 0.43 },
    { frequency: 18.7, before: 0.4, after: 0.41 },
    { frequency: 19.4, before: 0.38, after: 0.39 },
    { frequency: 20.1, before: 0.35, after: 0.36 },
    { frequency: 20.8, before: 0.33, after: 0.34 },
    { frequency: 21.5, before: 0.31, after: 0.31 },
    { frequency: 22.2, before: 0.29, after: 0.29 },
    { frequency: 22.9, before: 0.27, after: 0.27 },
    { frequency: 23.6, before: 0.26, after: 0.26 },
    { frequency: 24.3, before: 0.24, after: 0.24 },
    { frequency: 25, before: 0.22, after: 0.22 },
    { frequency: 25.7, before: 0.21, after: 0.2 },
    { frequency: 26.4, before: 0.19, after: 0.19 },
    { frequency: 27.1, before: 0.18, after: 0.18 },
    { frequency: 27.8, before: 0.16, after: 0.17 },
    { frequency: 28.5, before: 0.15, after: 0.15 },
    { frequency: 29.2, before: 0.14, after: 0.14 },
  ],
};

function round(value: number, digits = 3) {
  return Number(value.toFixed(digits));
}

function percentChange(baseline: number, optimized: number) {
  if (!baseline) return 0;
  return round(((optimized - baseline) / baseline) * 100, 1);
}

function clonePeakQqEvidence(source: PeakQqEvidence): PeakQqEvidence {
  return {
    beforePeaks: [...source.beforePeaks],
    afterPeaks: [...source.afterPeaks],
  };
}

function resolvePeakQqEvidence(source: EvidenceMetricSource): PeakQqEvidence {
  const beforePeaks = source.beforePeaks?.filter((value) =>
    Number.isFinite(value),
  );
  const afterPeaks = source.afterPeaks?.filter((value) => Number.isFinite(value));

  if (beforePeaks?.length && afterPeaks?.length) {
    return {
      beforePeaks: [...beforePeaks],
      afterPeaks: [...afterPeaks],
    };
  }

  if (!source.metricKey) {
    return {
      beforePeaks: [],
      afterPeaks: [],
    };
  }

  return clonePeakQqEvidence(
    defaultPeakQqEvidenceMap[source.metricKey] ??
      defaultPeakQqEvidenceMap.nacelle_acceleration,
  );
}

function resolveEnergySpectrumEvidence(
  source: EvidenceMetricSource,
): EnergySpectrumPoint[] {
  const energySpectrum = source.energySpectrum?.filter(
    (point) =>
      Number.isFinite(point.frequency) &&
      Number.isFinite(point.before) &&
      Number.isFinite(point.after),
  );

  if (energySpectrum?.length) {
    return energySpectrum.map((point) => ({ ...point }));
  }

  if (!source.metricKey) return [];

  return (
    defaultEnergySpectrumEvidenceMap[source.metricKey] ??
    defaultEnergySpectrumEvidenceMap.nacelle_acceleration
  ).map((point) => ({ ...point }));
}

function weightedRms(samples: Array<{ value: number; weight: number }>) {
  const totalWeight = samples.reduce((sum, item) => sum + item.weight, 0);
  if (!totalWeight) return 0;
  const weightedSquare = samples.reduce(
    (sum, item) => sum + item.value * item.value * item.weight,
    0,
  );
  return Math.sqrt(weightedSquare / totalWeight);
}

function weightedQuantile(
  samples: Array<{ value: number; weight: number }>,
  quantile: number,
) {
  const ordered = [...samples].sort((a, b) => a.value - b.value);
  const totalWeight = ordered.reduce((sum, item) => sum + item.weight, 0);
  if (!totalWeight) return 0;
  const target = totalWeight * quantile;
  let cumulative = 0;

  for (const item of ordered) {
    cumulative += item.weight;
    if (cumulative >= target) {
      return item.value;
    }
  }

  return ordered[ordered.length - 1]?.value ?? 0;
}

function buildResponseDistributions(
  damageSeries: number[],
  source: EvidenceMetricSource,
  shockSeries: number[] = [],
  bias = 0,
) {
  const peak = Math.max(...damageSeries, 0.0001);
  const base = Number(source.measurementBase ?? 1);
  const scale = Number(source.measurementScale ?? 1);
  const spread = Number(
    source.measurementSpread ?? Math.max(scale * 0.12, 0.1),
  );
  const shockPeak = Math.max(...shockSeries, 0.0001);
  const offsets = [-1.4, -0.95, -0.6, -0.25, 0, 0.2, 0.55, 0.9, 1.35];

  return damageSeries.map((value, index) => {
    const normalized = value / peak;
    const shockFactor = shockSeries.length
      ? (shockSeries[index % shockSeries.length] ?? 0) / shockPeak - 0.5
      : 0;
    const center =
      base +
      normalized * scale +
      Math.sin(index * 0.45) * spread * 0.35 +
      shockFactor * spread * 0.45 +
      bias;
    const localSpread = spread * (0.6 + normalized * 0.9);

    return offsets.map((offset, sampleIndex) =>
      Number(
        (
          center +
          offset * localSpread +
          Math.cos((index + sampleIndex) * 0.6) * localSpread * 0.08
        ).toFixed(3),
      ),
    );
  });
}

function buildWindowLabels(length: number) {
  const defaultLabels = ['0.5s', '1s', '2s', '5s', '10s', '20s'];
  if (length <= defaultLabels.length) {
    return defaultLabels.slice(0, length);
  }
  return Array.from(
    { length },
    (_, index) => defaultLabels[index] ?? `${index + 1}s`,
  );
}

function buildWindowMetrics(
  distributions: number[][],
  windowLabels: string[] = [],
) {
  const total = distributions.length;
  const windowCount = Math.min(
    6,
    Math.max(4, total ? Math.ceil(total / 6) : 0),
  );
  const chunkSize = Math.max(1, Math.ceil(total / Math.max(windowCount, 1)));
  const metrics: Array<{
    label: string;
    rms: number;
    p95: number;
    peak: number;
  }> = [];

  for (let index = 0; index < total; index += chunkSize) {
    const values = distributions.slice(index, index + chunkSize).flat();
    if (!values.length) continue;
    const weighted = values.map((value) => ({ value, weight: 1 }));
    metrics.push({
      label:
        windowLabels[metrics.length] ??
        buildWindowLabels(windowCount)[metrics.length],
      rms: weightedRms(weighted),
      p95: weightedQuantile(weighted, 0.95),
      peak: Math.max(...values),
    });
  }

  return metrics.length
    ? metrics
    : buildWindowLabels(4).map((label) => ({
        label,
        rms: 0,
        p95: 0,
        peak: 0,
      }));
}

export function buildOptimizationEvidence(
  meanBins: string[],
  amplitudeBins: string[],
  source: EvidenceMetricSource,
): OptimizationEvidence {
  void meanBins;
  void amplitudeBins;

  const unit = source.measurementUnit ?? '';
  const peakQqEvidence = resolvePeakQqEvidence(source);
  const energySpectrum = resolveEnergySpectrumEvidence(source);

  const baselineWindowDistributions = buildResponseDistributions(
    source.baselineDamage ?? [],
    source,
    source.baselineShock,
    0,
  );
  const optimizedWindowDistributions = buildResponseDistributions(
    source.optimizedDamage ?? [],
    source,
    source.optimizedShock,
    -(source.measurementSpread ?? 0.1) * 0.18,
  );

  const rmsWindowLabels = source.rmsWindowLabels ?? buildWindowLabels(6);

  const baselineWindows = buildWindowMetrics(
    baselineWindowDistributions,
    rmsWindowLabels,
  );
  const optimizedWindows = buildWindowMetrics(
    optimizedWindowDistributions,
    rmsWindowLabels,
  );
  const alignedWindowCount = Math.min(
    baselineWindows.length,
    optimizedWindows.length,
  );

  const rmsSeries = Array.from({ length: alignedWindowCount }, (_, index) => {
    const baseline = baselineWindows[index]?.rms ?? 0;
    const optimized = optimizedWindows[index]?.rms ?? 0;
    return {
      label:
        baselineWindows[index]?.label ?? rmsWindowLabels[index] ?? `${index + 1}s`,
      baseline: round(baseline),
      optimized: round(optimized),
      changePct: percentChange(baseline, optimized),
    };
  });

  const rmsImprovedWindows = rmsSeries.filter(
    (item) => item.optimized < item.baseline,
  ).length;
  const p95ImprovedWindows = Array.from(
    { length: alignedWindowCount },
    (_, index) =>
      (optimizedWindows[index]?.p95 ?? 0) < (baselineWindows[index]?.p95 ?? 0),
  ).filter(Boolean).length;
  const peakImprovedWindows = Array.from(
    { length: alignedWindowCount },
    (_, index) =>
      (optimizedWindows[index]?.peak ?? 0) <
      (baselineWindows[index]?.peak ?? 0),
  ).filter(Boolean).length;

  const windowBase = Math.max(alignedWindowCount, 1);
  const stabilitySeries: EvidenceStabilityDatum[] = [
    {
      key: 'rmsDropWindowRatio',
      value: round((rmsImprovedWindows / windowBase) * 100, 1),
    },
    {
      key: 'p95DropWindowRatio',
      value: round((p95ImprovedWindows / windowBase) * 100, 1),
    },
    {
      key: 'peakDropWindowRatio',
      value: round((peakImprovedWindows / windowBase) * 100, 1),
    },
  ];

  return {
    unit,
    rmsSeries,
    peakQqEvidence,
    stabilitySeries,
    energySpectrum,
  };
}
