export type DataAcquisitionMetricStatus = 'normal' | 'warning' | 'offline';
export type DeviceCommStatus = 'online' | 'warning' | 'offline';
export type DataAcquisitionTopMetricKey =
  | 'writeRate'
  | 'avgDelay'
  | 'p95Delay'
  | 'onlineDevices'
  | 'activeAlerts'
  | 'syncError'
  | 'integrityRate'
  | 'abnormalRate'
  | 'todayIncrement'
  | 'qualityLevel'
  | 'availableData'
  | 'totalData';
export type DataQualitySyncBinKey = 'lt10ms' | 'ms10to20' | 'ms20to50' | 'ms50to100' | 'gt100ms';
export type DataQualityAnomalyKey = 'missing' | 'outOfRange' | 'duplicate' | 'jump' | 'timeMisalignment';
export type DataQualityLatencyKey = 'p50' | 'p75' | 'p90' | 'p95' | 'p99';
export type ChannelCompositionKey = 'turbine' | 'lidar' | 'control' | 'reserved';
export type ChannelHealthMetricKey = 'packetLoss' | 'jitter' | 'avgDelay' | 'bandwidthHeadroom';
export type StoragePartitionKey = 'scadaRaw' | 'lidarTimeseries' | 'analysisResult' | 'archive';
export type ComputeServiceKey = 'collector' | 'cleaning' | 'quality' | 'analysis' | 'index' | 'forwarder';

export interface DataAcquisitionTopMetric {
  key: DataAcquisitionTopMetricKey;
  value: number | string;
  unit?: string;
  precision?: number;
  trend?: number;
  status?: DataAcquisitionMetricStatus;
}

export interface DeviceCommItem {
  id: string;
  type: 'turbine' | 'lidar';
  status: DeviceCommStatus;
  delay: number;
  signal: number;
  packetLoss: number;
  heartbeatSec: number;
  anomalies: number;
}

export interface DataCollectionMock {
  topMetrics: DataAcquisitionTopMetric[];
  deviceCommStatus: {
    devices: DeviceCommItem[];
  };
  dataQualityAnalysis: DataQualityAnalysisData;
  channelResource: ChannelResourceData;
  storageResource: StorageResourceData;
  computeResource: ComputeResourceData;
}

export interface DataQualityTrendPoint {
  time: string;
  value: number;
}

export interface DataQualityBinItem {
  key: DataQualitySyncBinKey;
  value: number;
}

export interface DataQualityAnomalyItem {
  key: DataQualityAnomalyKey;
  value: number;
  count: number;
}

export interface DataQualityLatencyItem {
  key: DataQualityLatencyKey;
  value: number;
}

export interface DataQualityAnalysisData {
  completenessTrend: DataQualityTrendPoint[];
  syncDiffBins: DataQualityBinItem[];
  anomalyRatio: DataQualityAnomalyItem[];
  latencyQuantiles: DataQualityLatencyItem[];
}

export interface ChannelTrafficPoint {
  time: string;
  value: number;
}

export interface ChannelCompositionItem {
  key: ChannelCompositionKey;
  value: number;
}

export interface ChannelHealthMetric {
  key: ChannelHealthMetricKey;
  value: number;
  unit: '%' | 'ms';
}

export interface ChannelResourceData {
  utilization: number;
  currentTraffic: number;
  packetLoss: number;
  avgDelay: number;
  peakBandwidth: number;
  trafficTrend: ChannelTrafficPoint[];
  channelComposition: ChannelCompositionItem[];
  healthMetrics: ChannelHealthMetric[];
}

export interface StoragePartitionItem {
  key: StoragePartitionKey;
  used: number;
  total: number;
}

export interface StorageGrowthPoint {
  date: string;
  value: number;
}

export interface StorageResourceData {
  totalData: number;
  dailyGrowth: number;
  diskUsage: number;
  remainingSpace: number;
  partitions: StoragePartitionItem[];
  growthTrend30d: StorageGrowthPoint[];
}

export interface ComputeLoadTrendPoint {
  time: string;
  cpu: number;
  memory: number;
  delay: number;
}

export interface ComputeThroughputPoint {
  time: string;
  value: number;
}

export interface ComputeUsageMinutePoint {
  time: string;
  cpu: number;
  memory: number;
}

export interface ComputeServiceItem {
  key: ComputeServiceKey;
  cpu: number;
  memory: number;
  status: 'online' | 'warning' | 'offline';
  qps: number;
}

export interface ComputeResourceData {
  cpuUsage: number;
  memoryUsage: number;
  processingDelay: number;
  peakCapacity: number;
  loadTrend: ComputeLoadTrendPoint[];
  throughputTrend: ComputeThroughputPoint[];
  usageTrend1m: ComputeUsageMinutePoint[];
  services: ComputeServiceItem[];
}
import {
  dataAcquisitionBaseDevices,
  dataAcquisitionBaseTotals,
} from './fixtures';

function round(value: number, digits = 0) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function wave(step: number, speed: number, amplitude: number, phase = 0) {
  return Math.sin(step / speed + phase) * amplitude;
}


function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

function getDynamicDevices(step: number): DeviceCommItem[] {
  return dataAcquisitionBaseDevices.map((device, index) => {
    const phase = index * 0.37;
    if (device.status === 'offline') {
      return { ...device };
    }

    const typeDelayBias = device.type === 'lidar' ? -3 : 0;
    const delay = round(clamp(device.delay + wave(step, 2.5 + (index % 4), 4 + (index % 3), phase) + typeDelayBias, 8, 88));
    const signal = round(clamp(device.signal + wave(step, 3.8 + (index % 5), 3.2, phase + 0.4), 78, 100));
    const packetLoss = round(clamp(device.packetLoss + wave(step, 3.1 + (index % 3), 0.22, phase + 0.9), 0.1, 5), 1);
    const heartbeatSec = round(clamp(device.heartbeatSec + wave(step, 2.9 + (index % 4), 1.4, phase + 0.6), 1, 12));
    const anomalies = Math.max(0, Math.round(device.anomalies + wave(step, 4.4 + (index % 4), 1.6, phase + 1.2)));

    let status: DeviceCommStatus = 'online';
    if (delay >= 40 || signal <= 90 || packetLoss >= 0.8) {
      status = 'warning';
    }

    if (device.id === 'T30') {
      status = 'offline';
    }

    return {
      ...device,
      status,
      delay,
      signal,
      packetLoss,
      heartbeatSec,
      anomalies,
    };
  });
}

function getDataQualityAnalysis(step: number): DataQualityAnalysisData {
  return {
    completenessTrend: Array.from({ length: 30 }, (_, index) => ({
      time: `${index + 1}日`,
      value: round(
        99
          + wave(step, 4.6, 0.12, index * 0.22)
          + wave(step + index, 7.1, 0.08, index * 0.14),
        1,
      ),
    })),
    syncDiffBins: [
      { key: 'lt10ms', value: Math.max(34, Math.round(42 + wave(step, 3.2, 4))) },
      { key: 'ms10to20', value: Math.max(22, Math.round(31 + wave(step, 3.8, 3, 0.9))) },
      { key: 'ms20to50', value: Math.max(12, Math.round(18 + wave(step, 4.1, 2, 1.7))) },
      { key: 'ms50to100', value: Math.max(4, Math.round(7 + wave(step, 3.4, 1.5, 2.1))) },
      { key: 'gt100ms', value: Math.max(1, Math.round(2 + wave(step, 4.4, 0.8, 2.8))) },
    ],
    anomalyRatio: [
      { key: 'missing', value: round(0.08 + wave(step, 4.2, 0.01, 0.6), 2), count: Math.max(72, Math.round(96 + wave(step, 3.5, 14))) },
      { key: 'outOfRange', value: round(0.05 + wave(step, 4.8, 0.008, 1.2), 2), count: Math.max(48, Math.round(61 + wave(step, 4.1, 9, 0.4))) },
      { key: 'duplicate', value: round(0.03 + wave(step, 3.9, 0.006, 1.9), 2), count: Math.max(28, Math.round(38 + wave(step, 4.7, 6, 1.1))) },
      { key: 'jump', value: round(0.02 + wave(step, 4.5, 0.005, 2.4), 2), count: Math.max(18, Math.round(26 + wave(step, 4.9, 5, 0.8))) },
      { key: 'timeMisalignment', value: round(0.02 + wave(step, 3.7, 0.004, 2.9), 2), count: Math.max(16, Math.round(21 + wave(step, 4.3, 4, 1.6))) },
    ],
    latencyQuantiles: [
      { key: 'p50', value: Math.max(60, Math.round(72 + wave(step, 4.1, 5))) },
      { key: 'p75', value: Math.max(76, Math.round(88 + wave(step, 4.6, 6, 0.6))) },
      { key: 'p90', value: Math.max(92, Math.round(105 + wave(step, 4.9, 7, 1.1))) },
      { key: 'p95', value: Math.max(106, Math.round(120 + wave(step, 5.4, 8, 1.7))) },
      { key: 'p99', value: Math.max(135, Math.round(155 + wave(step, 6.1, 10, 2.2))) },
    ],
  };
}

function getChannelResource(step: number): ChannelResourceData {
  const trafficTrend = Array.from({ length: 12 }, (_, index) => {
    const seconds = index * 5;
    return {
      time: `${String(seconds).padStart(2, '0')}s`,
      value: round(
        11.2
          + wave(step, 3.6, 1.3, index * 0.34)
          + wave(step + index, 5.2, 0.8, index * 0.21),
        1,
      ),
    };
  });
  const currentTraffic = trafficTrend[trafficTrend.length - 1]?.value ?? 12;
  const utilization = clamp(round(45 + wave(step, 5.4, 5.5, 0.5), 1), 32, 78);
  const packetLoss = clamp(round(0.2 + wave(step, 4.8, 0.15, 1.6), 2), 0.05, 1.2);
  const avgDelay = clamp(round(18 + wave(step, 4.2, 4.8, 0.9), 1), 10, 38);
  const peakBandwidth = round(Math.max(...trafficTrend.map((item) => item.value)) + 5.3, 1);

  return {
    utilization,
    currentTraffic,
    packetLoss,
    avgDelay,
    peakBandwidth,
    trafficTrend,
    channelComposition: [
      { key: 'turbine', value: 30 },
      { key: 'lidar', value: 5 },
      { key: 'control', value: 6 },
      { key: 'reserved', value: 3 },
    ],
    healthMetrics: [
      { key: 'packetLoss', value: packetLoss, unit: '%' },
      { key: 'jitter', value: clamp(round(6 + wave(step, 4.7, 1.6, 1.3), 1), 3, 12), unit: 'ms' },
      { key: 'avgDelay', value: avgDelay, unit: 'ms' },
      { key: 'bandwidthHeadroom', value: round(100 - utilization, 1), unit: '%' },
    ],
  };
}

function getStorageResource(step: number): StorageResourceData {
  const partitions: StoragePartitionItem[] = [
    {
      key: 'scadaRaw',
      used: round(clamp(7.8 + wave(step, 5.4, 0.28, 0.2), 7.1, 8.8), 1),
      total: 10,
    },
    {
      key: 'lidarTimeseries',
      used: round(clamp(8.6 + wave(step, 5.9, 0.32, 0.7), 7.8, 9.9), 1),
      total: 12,
    },
    {
      key: 'analysisResult',
      used: round(clamp(5.1 + wave(step, 6.4, 0.24, 1.3), 4.6, 6.2), 1),
      total: 8,
    },
    {
      key: 'archive',
      used: round(clamp(7.1 + wave(step, 6.8, 0.35, 1.8), 6.3, 8.6), 1),
      total: 15,
    },
  ];

  const totalCapacity = partitions.reduce((sum, item) => sum + item.total, 0);
  const totalUsed = partitions.reduce((sum, item) => sum + item.used, 0);
  const startDate = new Date('2026-02-13');
  const growthTrend30d = Array.from({ length: 30 }, (_, index) => {
    const current = new Date(startDate);
    current.setDate(startDate.getDate() + index);
    const month = `${current.getMonth() + 1}`.padStart(2, '0');
    const day = `${current.getDate()}`.padStart(2, '0');

    return {
      date: `${month}-${day}`,
      value: round(
        286
          + index * 1.2
          + wave(step, 5.2, 10, index * 0.18)
          + wave(step + index, 7.4, 8, index * 0.11),
      ),
    };
  });

  return {
    totalData: round(28.6 + step * 0.008, 1),
    dailyGrowth: growthTrend30d[growthTrend30d.length - 1]?.value ?? 320,
    diskUsage: round((totalUsed / Math.max(totalCapacity, 1)) * 100, 1),
    remainingSpace: round(totalCapacity - totalUsed, 1),
    partitions,
    growthTrend30d,
  };
}

function getComputeResource(step: number): ComputeResourceData {
  const loadTrend = [
    { time: '00:00', cpu: round(28 + wave(step, 5.1, 3.2, 0.2)), memory: round(42 + wave(step, 5.6, 3.4, 0.6)), delay: round(102 + wave(step, 4.9, 10, 0.9)) },
    { time: '02:00', cpu: round(30 + wave(step, 5.4, 3.5, 0.5)), memory: round(43 + wave(step, 5.2, 3.8, 0.9)), delay: round(108 + wave(step, 5.1, 10, 1.2)) },
    { time: '04:00', cpu: round(31 + wave(step, 5.0, 3.1, 0.8)), memory: round(44 + wave(step, 5.5, 3.5, 1.1)), delay: round(112 + wave(step, 4.8, 11, 1.5)) },
    { time: '06:00', cpu: round(33 + wave(step, 4.8, 3.6, 1.1)), memory: round(46 + wave(step, 5.1, 3.9, 1.5)), delay: round(118 + wave(step, 4.6, 11, 1.8)) },
    { time: '08:00', cpu: round(37 + wave(step, 4.6, 4.1, 1.4)), memory: round(49 + wave(step, 4.8, 4.2, 1.9)), delay: round(125 + wave(step, 4.4, 12, 2.1)) },
    { time: '10:00', cpu: round(41 + wave(step, 4.4, 4.6, 1.8)), memory: round(53 + wave(step, 4.6, 4.4, 2.3)), delay: round(132 + wave(step, 4.2, 12, 2.5)) },
    { time: '12:00', cpu: round(45 + wave(step, 4.1, 5.1, 2.1)), memory: round(56 + wave(step, 4.4, 4.7, 2.7)), delay: round(141 + wave(step, 4.0, 13, 2.9)) },
    { time: '14:00', cpu: round(43 + wave(step, 4.6, 4.7, 2.4)), memory: round(55 + wave(step, 4.8, 4.5, 3.1)), delay: round(136 + wave(step, 4.5, 12, 3.2)) },
    { time: '16:00', cpu: round(39 + wave(step, 5.0, 4.2, 2.8)), memory: round(52 + wave(step, 5.1, 4.1, 3.5)), delay: round(128 + wave(step, 4.9, 11, 3.6)) },
    { time: '18:00', cpu: round(36 + wave(step, 5.3, 3.8, 3.1)), memory: round(49 + wave(step, 5.4, 3.8, 3.9)), delay: round(121 + wave(step, 5.1, 10, 4.0)) },
    { time: '20:00', cpu: round(34 + wave(step, 5.5, 3.5, 3.4)), memory: round(47 + wave(step, 5.7, 3.5, 4.2)), delay: round(116 + wave(step, 5.3, 10, 4.4)) },
    { time: '22:00', cpu: round(33 + wave(step, 5.7, 3.3, 3.8)), memory: round(46 + wave(step, 5.9, 3.3, 4.6)), delay: round(114 + wave(step, 5.5, 9, 4.8)) },
    { time: '24:00', cpu: round(35 + wave(step, 5.2, 3.7, 4.1)), memory: round(48 + wave(step, 5.4, 3.6, 5.0)), delay: round(120 + wave(step, 5.0, 10, 5.1)) },
  ];
  const throughputTrend = [
    { time: '00:00', value: round(18.2 + wave(step, 5.0, 0.8, 0.2), 1) },
    { time: '02:00', value: round(19.1 + wave(step, 4.8, 0.9, 0.6), 1) },
    { time: '04:00', value: round(20.0 + wave(step, 4.6, 1.0, 1.0), 1) },
    { time: '06:00', value: round(21.4 + wave(step, 4.4, 1.2, 1.4), 1) },
    { time: '08:00', value: round(23.6 + wave(step, 4.2, 1.4, 1.8), 1) },
    { time: '10:00', value: round(25.1 + wave(step, 4.0, 1.4, 2.2), 1) },
    { time: '12:00', value: round(26.3 + wave(step, 3.8, 1.5, 2.6), 1) },
    { time: '14:00', value: round(25.4 + wave(step, 4.1, 1.4, 3.0), 1) },
    { time: '16:00', value: round(24.2 + wave(step, 4.4, 1.2, 3.4), 1) },
    { time: '18:00', value: round(22.8 + wave(step, 4.6, 1.1, 3.8), 1) },
    { time: '20:00', value: round(21.7 + wave(step, 4.9, 1.0, 4.2), 1) },
    { time: '22:00', value: round(20.9 + wave(step, 5.1, 0.9, 4.6), 1) },
    { time: '24:00', value: round(21.3 + wave(step, 5.3, 0.9, 5.0), 1) },
  ];
  const usageTrend1m = Array.from({ length: 12 }, (_, index) => {
    const seconds = index * 5;
    return {
      time: `${String(seconds).padStart(2, '0')}s`,
      cpu: clamp(round(34 + wave(step, 2.1, 5.2, index * 0.42)), 22, 72),
      memory: clamp(round(47 + wave(step, 2.6, 4.8, index * 0.36 + 0.8)), 34, 78),
    };
  });
  const services: ComputeServiceItem[] = [
    { key: 'collector', cpu: clamp(round(22 + wave(step, 4.7, 4.2, 0.3)), 14, 38), memory: clamp(round(31 + wave(step, 5.1, 4.5, 0.7)), 20, 44), status: 'online' as const, qps: round(5.8 + wave(step, 4.6, 0.7, 0.5), 1) },
    { key: 'cleaning', cpu: clamp(round(38 + wave(step, 4.5, 5.1, 1.1)), 24, 54), memory: clamp(round(46 + wave(step, 4.9, 5.0, 1.5)), 30, 62), status: 'online' as const, qps: round(4.9 + wave(step, 4.3, 0.6, 1.0), 1) },
    { key: 'quality', cpu: clamp(round(41 + wave(step, 4.2, 5.4, 1.8)), 28, 58), memory: clamp(round(52 + wave(step, 4.6, 5.2, 2.0)), 36, 66), status: 'online' as const, qps: round(4.2 + wave(step, 4.1, 0.6, 1.7), 1) },
    { key: 'analysis', cpu: clamp(round(57 + wave(step, 4.0, 6.6, 2.3)), 40, 76), memory: clamp(round(63 + wave(step, 4.4, 6.4, 2.6)), 44, 79), status: 'warning' as const, qps: round(6.6 + wave(step, 3.9, 0.8, 2.4), 1) },
    { key: 'index', cpu: clamp(round(29 + wave(step, 4.8, 4.1, 3.1)), 18, 42), memory: clamp(round(35 + wave(step, 5.0, 4.0, 3.3)), 24, 48), status: 'online' as const, qps: round(2.8 + wave(step, 4.5, 0.5, 3.0), 1) },
    { key: 'forwarder', cpu: clamp(round(18 + wave(step, 5.2, 3.5, 3.7)), 10, 30), memory: clamp(round(26 + wave(step, 5.5, 3.8, 4.0)), 16, 38), status: 'online' as const, qps: round(3.1 + wave(step, 4.9, 0.5, 3.5), 1) },
  ];

  return {
    cpuUsage: loadTrend[loadTrend.length - 1]?.cpu ?? 35,
    memoryUsage: loadTrend[loadTrend.length - 1]?.memory ?? 48,
    processingDelay: loadTrend[loadTrend.length - 1]?.delay ?? 120,
    peakCapacity: round(30 + wave(step, 6.2, 1.4, 0.9), 1),
    loadTrend,
    throughputTrend,
    usageTrend1m,
    services,
  };
}

export function getDataAcquisitionTopMetrics(step: number): DataAcquisitionTopMetric[] {
  const devices = getDynamicDevices(step);
  const onlineDevices = devices.filter((item) => item.status === 'online').length;
  const activeAlerts = devices.filter((item) => item.status === 'warning').length;
  const nonOfflineDevices = devices.filter((item) => item.status !== 'offline');
  const avgDelay = round(nonOfflineDevices.reduce((sum, item) => sum + item.delay, 0) / Math.max(nonOfflineDevices.length, 1));
  const p95Delay = round(
    [...nonOfflineDevices].sort((a, b) => a.delay - b.delay)[Math.max(0, Math.floor(nonOfflineDevices.length * 0.95) - 1)]?.delay ?? avgDelay,
  );
  const writeRate = round(12 + wave(step, 1.8, 1.4) + wave(step, 4.6, 0.5, 0.8), 1);
  const syncError = round(16 + wave(step, 2.1, 5.2) + wave(step, 5.1, 1.4, 0.3));
  const integrityRate = round(99.5 + wave(step, 3.4, 0.2, 0.7), 1);
  const abnormalRate = round(0.24 + wave(step, 2.6, 0.08, 1.6), 2);
  const todayIncrement = round(dataAcquisitionBaseTotals.todayIncrement + step * 1.8 + wave(step, 3.7, 6, 0.5));
  const availableData = round(dataAcquisitionBaseTotals.availableData + step * 0.006, 1);
  const totalData = round(dataAcquisitionBaseTotals.totalData + step * 0.008, 1);
  const qualityLevel = syncError <= 20 && activeAlerts <= 2 ? 'A' : 'B';

  return [
    { key: 'writeRate', value: writeRate, unit: 'k/s', precision: 1, trend: round(writeRate - 12, 1), status: 'normal' },
    { key: 'avgDelay', value: avgDelay, unit: 'ms', precision: 0, trend: round(84 - avgDelay, 1), status: avgDelay > 90 ? 'warning' : 'normal' },
    { key: 'p95Delay', value: p95Delay, unit: 'ms', precision: 0, trend: round(122 - p95Delay, 1), status: p95Delay > 132 ? 'warning' : 'normal' },
    { key: 'onlineDevices', value: onlineDevices, unit: '台', precision: 0, trend: round(onlineDevices - 35, 0), status: onlineDevices < 35 ? 'warning' : 'normal' },
    { key: 'activeAlerts', value: activeAlerts, unit: '条', precision: 0, trend: -activeAlerts, status: activeAlerts >= 3 ? 'warning' : 'normal' },
    { key: 'syncError', value: syncError, unit: 'ms', precision: 0, trend: round(16 - syncError, 1), status: syncError > 20 ? 'warning' : 'normal' },
    { key: 'integrityRate', value: integrityRate, unit: '%', precision: 1, trend: round(integrityRate - 99.5, 2), status: 'normal' },
    { key: 'abnormalRate', value: abnormalRate, unit: '%', precision: 2, trend: round(0.24 - abnormalRate, 2), status: abnormalRate > 0.28 ? 'warning' : 'normal' },
    { key: 'todayIncrement', value: todayIncrement, unit: 'GB', precision: 0, trend: round(todayIncrement - dataAcquisitionBaseTotals.todayIncrement, 0), status: 'normal' },
    { key: 'qualityLevel', value: qualityLevel, status: qualityLevel === 'A' ? 'normal' : 'warning' },
    { key: 'availableData', value: availableData, unit: 'TB', precision: 1, trend: round(availableData - dataAcquisitionBaseTotals.availableData, 1), status: 'normal' },
    { key: 'totalData', value: totalData, unit: 'TB', precision: 1, trend: round(totalData - dataAcquisitionBaseTotals.totalData, 1), status: 'normal' },
  ];
}

export function getDataCollectionMock(step: number): DataCollectionMock {
  return {
    topMetrics: getDataAcquisitionTopMetrics(step),
    deviceCommStatus: {
      devices: getDynamicDevices(step),
    },
    dataQualityAnalysis: getDataQualityAnalysis(step),
    channelResource: getChannelResource(step),
    storageResource: getStorageResource(step),
    computeResource: getComputeResource(step),
  };
}
