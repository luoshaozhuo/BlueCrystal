import type {
  ConsistencyAlignmentData,
  DataQualitySummary,
  LidarDeviceInfo,
  LidarForwardComposite3DResponse,
  LidarInflowProfilePanelData,
  LidarTopMetricItem,
  LidarTurbineOption,
  RealtimeWindWaveResponse,
  TransferFunctionData,
  WindRoseTiStats,
} from '@/types/lidar';
import {
  generateConsistencyAlignmentData,
  generateDataQualitySummary,
  generateLidarDeviceInfo,
  generateLidarForwardComposite3DData,
  generateLidarInflowProfilePanelData,
  generateLidarTopMetrics,
  generateLidarTurbineOptions,
  generateTopRealtimeWindWave,
  resetTopRealtimeWindWave,
  generateTransferFunctionData,
  generateWindRoseTiStats,
} from '@/mock/lidar';

let activeLidarTurbineId = 'WT-07';

function resolveWithLatency<T>(factory: () => T, delay = 120): Promise<T> {
  return new Promise((resolve) => {
    window.setTimeout(() => resolve(factory()), delay);
  });
}

export function setActiveLidarTurbine(turbineId: string) {
  activeLidarTurbineId = turbineId;
  resetTopRealtimeWindWave(turbineId);
}

export function getLidarTurbineOptions(): Promise<LidarTurbineOption[]> {
  return resolveWithLatency(generateLidarTurbineOptions, 90);
}

export function getLidarDeviceInfo(): Promise<LidarDeviceInfo> {
  return resolveWithLatency(() => generateLidarDeviceInfo(activeLidarTurbineId), 90);
}

export function getLidarTopMetrics(): Promise<LidarTopMetricItem[]> {
  return resolveWithLatency(() => generateLidarTopMetrics(activeLidarTurbineId), 90);
}

export function getTopRealtimeWindWave(): Promise<RealtimeWindWaveResponse> {
  return resolveWithLatency(() => generateTopRealtimeWindWave(activeLidarTurbineId), 60);
}

export function getLidarForwardComposite3DData(): Promise<LidarForwardComposite3DResponse> {
  return resolveWithLatency(() => generateLidarForwardComposite3DData(activeLidarTurbineId), 150);
}

export function getLidarInflowProfilePanelData(): Promise<LidarInflowProfilePanelData> {
  return resolveWithLatency(() => generateLidarInflowProfilePanelData(activeLidarTurbineId), 140);
}

export function getWindRoseTiStats(): Promise<WindRoseTiStats> {
  return resolveWithLatency(generateWindRoseTiStats, 160);
}

export function getTransferFunctionData(): Promise<TransferFunctionData> {
  return resolveWithLatency(generateTransferFunctionData, 180);
}

export function getConsistencyAlignmentData(): Promise<ConsistencyAlignmentData> {
  return resolveWithLatency(generateConsistencyAlignmentData, 170);
}

export function getDataQualitySummary(): Promise<DataQualitySummary> {
  return resolveWithLatency(generateDataQualitySummary, 110);
}
