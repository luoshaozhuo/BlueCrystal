import type { AmplitudeStructureComparisonData } from './amplitude-structure';
import {
  loadMitigationHighAmplitudeBins,
  loadMitigationKpiList,
  loadMitigationMeanBins,
  loadMitigationMetricSources,
  loadMitigationRangeBins,
  loadMitigationTurbineMeta,
  loadMitigationTurbineOptions,
  type LoadMetricKey,
} from './fixtures';
import type { MarkovMatrixComparisonData } from './markov-matrix';
import {
  buildOptimizationEvidence,
} from './optimization-evidence';

export interface LoadMitigationMetricConfig {
  migrationData: MarkovMatrixComparisonData;
  structureData: AmplitudeStructureComparisonData;
  riskData: AmplitudeStructureComparisonData;
  evidence: ReturnType<typeof buildOptimizationEvidence>;
}

function normalizeByRow(matrix: number[][], rowBins: string[], columnBins: string[]) {
  return rowBins.map((rowBin, rowIndex) => {
    const rowValues = columnBins.map((_, columnIndex) => Number(matrix?.[rowIndex]?.[columnIndex] ?? 0));
    const safeValues = rowValues.map((value) => (Number.isFinite(value) ? Math.max(value, 0) : 0));
    const total = safeValues.reduce((sum, value) => sum + value, 0);
    const values = total ? safeValues.map((value) => Number((value / total).toFixed(6))) : safeValues.map(() => 0);
    return { meanBin: rowBin, values };
  });
}

function normalizeMatrixByTotals(matrix: number[][], rowCount: number, columnCount: number) {
  const safeMatrix = Array.from({ length: rowCount }, (_, rowIndex) =>
    Array.from({ length: columnCount }, (_, columnIndex) => {
      const value = Number(matrix?.[rowIndex]?.[columnIndex] ?? 0);
      return Number.isFinite(value) ? Math.max(value, 0) : 0;
    }),
  );
  const total = safeMatrix.reduce((sum, row) => sum + row.reduce((rowSum, value) => rowSum + value, 0), 0);
  if (!total) {
    return safeMatrix.map((row) => row.map(() => 0));
  }
  return safeMatrix.map((row) => row.map((value) => Number((value / total).toFixed(6))));
}

export function createLoadMitigationMetricConfigMap(): Record<LoadMetricKey, LoadMitigationMetricConfig> {
  return Object.entries(loadMitigationMetricSources).reduce((result, [key, config]) => {
    const typedKey = key as LoadMetricKey;
    const migrationData: MarkovMatrixComparisonData = {
      meanBins: loadMitigationMeanBins,
      amplitudeBins: loadMitigationRangeBins,
      baseline: normalizeMatrixByTotals(config.baselineMatrix, loadMitigationRangeBins.length, loadMitigationMeanBins.length),
      optimized: normalizeMatrixByTotals(config.optimizedMatrix, loadMitigationRangeBins.length, loadMitigationMeanBins.length),
    };
    const structureData: AmplitudeStructureComparisonData = {
      meanBins: loadMitigationRangeBins,
      amplitudeBins: loadMitigationMeanBins,
      baseline: normalizeByRow(config.baselineMatrix, loadMitigationRangeBins, loadMitigationMeanBins),
      optimized: normalizeByRow(config.optimizedMatrix, loadMitigationRangeBins, loadMitigationMeanBins),
    };
    result[typedKey] = {
      migrationData,
      structureData,
      riskData: structureData,
      evidence: buildOptimizationEvidence(loadMitigationMeanBins, loadMitigationRangeBins, config),
    };
    return result;
  }, {} as Record<LoadMetricKey, LoadMitigationMetricConfig>);
}

export function createLoadMitigationPageMock() {
  const metricConfigMap = createLoadMitigationMetricConfigMap();

  return {
    turbineOptions: loadMitigationTurbineOptions,
    turbineMeta: loadMitigationTurbineMeta,
    kpiList: loadMitigationKpiList,
    highAmplitudeBins: loadMitigationHighAmplitudeBins,
    metricConfigMap,
  };
}
