import type {
  ConsistencyAlignmentData,
  ConsistencyAlignmentPoint,
  DataQualitySummary,
  LidarDeviceInfo,
  LidarInflowProfilePanelData,
  LidarInflowProfilePoint,
  LidarForwardComposite3DResponse,
  LidarRawPoint3D,
  LidarSynthPoint3D,
  LidarTopMetricItem,
  LidarTurbineOption,
  RealtimeWindWavePoint,
  RealtimeWindWaveResponse,
  TransferFunctionData,
  TransferFunctionPoint,
  WindRoseSector,
  WindRoseTiStats,
} from '@/types/lidar';
import {
  lidarModeMapFixture,
  lidarTurbineOptionsFixture,
} from './fixtures';

let realtimeWaveBuffer: RealtimeWindWavePoint[] = [];
let realtimeWaveSeed = '';
let realtimeWaveIndex = 0;
let realtimeWaveBase = 8.9;
let realtimeWaveClock = new Date('2026-03-13T14:36:00');
let realtimeWaveJustReset = true;
const forwardCompositeStepMap = new Map<string, number>();

function getTurbineOrdinal(turbineId: string) {
  const match = turbineId.match(/(\d+)/);
  return match ? match[1].padStart(3, '0') : '000';
}

function calculateHubWindSpeedAt(step: number, rand: () => number, base: number) {
  const value =
    base +
    0.45 * Math.sin((2 * Math.PI * step) / 48) +
    0.18 * Math.sin((2 * Math.PI * step) / 13) +
    noise(rand, 0.08);
  return round(clamp(value, 6.5, 11.5));
}

function calculateHubDirectionAt(step: number, rand: () => number, base: number) {
  const value =
    base +
    8 * Math.sin((2 * Math.PI * step) / 55) +
    3 * Math.sin((2 * Math.PI * step) / 17) +
    noise(rand, 1.8);
  const normalized = ((value % 360) + 360) % 360;
  return round(normalized, 0);
}

function calculateTiAt(step: number, rand: () => number) {
  const ti = 100 * (0.11 + 0.025 * Math.sin((2 * Math.PI * step) / 41) + noise(rand, 0.006));
  return round(clamp(ti, 7, 18), 1);
}

function ensureRealtimeWaveBuffer(turbineId: string) {
  if (realtimeWaveBuffer.length && realtimeWaveSeed === turbineId) {
    return;
  }

  const rand = createSeededRandom(`top-realtime-wave-${turbineId}`);
  realtimeWaveSeed = turbineId;
  realtimeWaveBase = 8.4 + rand();
  realtimeWaveIndex = 59;
  realtimeWaveClock = new Date('2026-03-13T14:36:00');
  realtimeWaveBuffer = Array.from({ length: 60 }, (_, index) => {
    const pointTime = new Date(realtimeWaveClock.getTime() - (59 - index) * 1000);
    const windSpeed =
      realtimeWaveBase +
      0.42 * Math.sin((2 * Math.PI * index) / 52) +
      0.16 * Math.sin((2 * Math.PI * index) / 15) +
      0.06 * Math.sin((2 * Math.PI * index) / 7) +
      noise(rand, 0.05);
    return {
      ts: formatTime(pointTime),
      windSpeed: round(clamp(windSpeed, 6.5, 11.5)),
    };
  });
}

export function resetTopRealtimeWindWave(turbineId: string) {
  realtimeWaveBuffer = [];
  realtimeWaveSeed = '';
  ensureRealtimeWaveBuffer(turbineId);
  realtimeWaveJustReset = true;
}

export function generateLidarTurbineOptions(): LidarTurbineOption[] {
  return lidarTurbineOptionsFixture.map((item) => ({ ...item }));
}

export function generateLidarDeviceInfo(turbineId: string): LidarDeviceInfo {
  const mode = lidarModeMapFixture[turbineId] ?? '3D';
  return {
    deviceModel: 'ZX300',
    deviceId: `LD-${getTurbineOrdinal(turbineId)}-${mode === '3D' ? '3001' : mode === '2D' ? '2201' : '1101'}`,
    scanMode: mode,
    scanLayers: 3,
    scanAngleRange: '±30°',
    sampleFrequencyHz: mode === '3D' ? 1 : 2,
  };
}

export function generateLidarTopMetrics(turbineId: string): LidarTopMetricItem[] {
  const rand = createSeededRandom(`top-metrics-${turbineId}`);
  const now = Math.floor(Date.now() / 1000);
  const baseWind = 8.2 + rand() * 1.4;
  const directionBase = 110 + rand() * 40;
  const speed = calculateHubWindSpeedAt(now, rand, baseWind);
  const direction = calculateHubDirectionAt(now, rand, directionBase);
  const ti = calculateTiAt(now, rand);
  const gustFactor = round(clamp(1.02 + 0.015 * ti + noise(rand, 0.02), 1.05, 1.35), 2);
  const verticalShear = round(clamp(0.16 + 0.05 * Math.sin((2 * Math.PI * now) / 70) + noise(rand, 0.015), 0.05, 0.32), 2);
  const horizontalShear = round(
    clamp(
      0.03 * Math.sin((2 * Math.PI * now) / 33) +
        0.02 * Math.sin((2 * Math.PI * now) / 11) +
        noise(rand, 0.012),
      -0.18,
      0.18,
    ),
    2,
  );

  const statusRoll = rand();
  const statusTone = statusRoll < 0.92 ? 'normal' : statusRoll < 0.98 ? 'warning' : 'offline';

  return [
    { key: 'deviceStatus', value: statusTone, status: statusTone },
    { key: 'hubSpeed', value: speed, unit: 'm/s', precision: 2, status: 'normal', trend: round(noise(rand, 0.18), 2) },
    { key: 'hubDirection', value: direction, unit: 'deg', precision: 0, status: 'normal', trend: round(noise(rand, 2.5), 1) },
    { key: 'ti1m', value: ti, unit: '%', precision: 1, status: ti > 15 ? 'warning' : 'normal', trend: round(noise(rand, 0.6), 1) },
    { key: 'gustFactor', value: gustFactor, unit: '-', precision: 2, status: gustFactor > 1.28 ? 'warning' : 'normal', trend: round(noise(rand, 0.03), 2) },
    { key: 'verticalShear', value: verticalShear, unit: '-', precision: 2, status: verticalShear > 0.26 ? 'warning' : 'normal', trend: round(noise(rand, 0.03), 2) },
    { key: 'horizontalShear', value: horizontalShear, unit: '-', precision: 2, status: Math.abs(horizontalShear) > 0.12 ? 'warning' : 'normal', trend: round(noise(rand, 0.03), 2) },
  ];
}

export function generateTopRealtimeWindWave(turbineId: string): RealtimeWindWaveResponse {
  ensureRealtimeWaveBuffer(turbineId);
  if (realtimeWaveJustReset) {
    realtimeWaveJustReset = false;
    const initialValues = realtimeWaveBuffer.map((item) => item.windSpeed);
    return {
      points: realtimeWaveBuffer.map((item) => ({ ...item })),
      current: round(initialValues[initialValues.length - 1]),
      mean60s: round(initialValues.reduce((sum, value) => sum + value, 0) / initialValues.length),
      min60s: round(Math.min(...initialValues)),
      max60s: round(Math.max(...initialValues)),
    };
  }
  const rand = createSeededRandom(`top-realtime-wave-step-${turbineId}-${realtimeWaveIndex}`);
  const previous = realtimeWaveBuffer[realtimeWaveBuffer.length - 1];
  realtimeWaveIndex += 1;
  realtimeWaveClock = new Date(realtimeWaveClock.getTime() + 1000);
  const target =
    realtimeWaveBase +
    0.45 * Math.sin((2 * Math.PI * realtimeWaveIndex) / 48) +
    0.15 * Math.sin((2 * Math.PI * realtimeWaveIndex) / 14);
  const nextWindSpeed = clamp(0.72 * previous.windSpeed + 0.28 * target + noise(rand, 0.05), 6.5, 11.5);

  realtimeWaveBuffer.shift();
  realtimeWaveBuffer.push({
    ts: formatTime(realtimeWaveClock),
    windSpeed: round(nextWindSpeed),
  });

  const values = realtimeWaveBuffer.map((item) => item.windSpeed);
  return {
    points: realtimeWaveBuffer.map((item) => ({ ...item })),
    current: round(values[values.length - 1]),
    mean60s: round(values.reduce((sum, value) => sum + value, 0) / values.length),
    min60s: round(Math.min(...values)),
    max60s: round(Math.max(...values)),
  };
}

function hashSeed(seed: string) {
  let h = 1779033703 ^ seed.length;
  for (let i = 0; i < seed.length; i += 1) {
    h = Math.imul(h ^ seed.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  return () => {
    h = Math.imul(h ^ (h >>> 16), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    h ^= h >>> 16;
    return h >>> 0;
  };
}

function createSeededRandom(seed: string) {
  const seedFn = hashSeed(seed);
  let state = seedFn();
  return () => {
    state += 0x6d2b79f5;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function noise(rand: () => number, amplitude: number) {
  return (rand() - 0.5) * 2 * amplitude;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function round(value: number, digits = 2) {
  return Number(value.toFixed(digits));
}

function pad(value: number) {
  return String(value).padStart(2, '0');
}

function formatTime(date: Date) {
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

function buildTimeline(count: number, stepSeconds: number, anchor: string) {
  const base = new Date(anchor);
  const points: Date[] = [];
  const start = new Date(base.getTime() - (count - 1) * stepSeconds * 1000);
  for (let index = 0; index < count; index += 1) {
    points.push(new Date(start.getTime() + index * stepSeconds * 1000));
  }
  return points;
}

function projectPolar(range: number, azimuth: number, elevation: number) {
  const azimuthRad = (azimuth * Math.PI) / 180;
  const elevationFactor = 1 - elevation / 32;
  return {
    x: round(range * Math.sin(azimuthRad) * elevationFactor, 1),
    y: round(range * Math.cos(azimuthRad) * (0.44 + elevation / 36), 1),
  };
}

function computeRegression(points: ConsistencyAlignmentPoint[]) {
  const count = points.length;
  const xMean = points.reduce((sum, item) => sum + item.lidarWindSpeed, 0) / count;
  const yMean = points.reduce((sum, item) => sum + item.nacelleWindSpeed, 0) / count;
  let covariance = 0;
  let varianceX = 0;
  let varianceY = 0;

  points.forEach((item) => {
    const dx = item.lidarWindSpeed - xMean;
    const dy = item.nacelleWindSpeed - yMean;
    covariance += dx * dy;
    varianceX += dx * dx;
    varianceY += dy * dy;
  });

  const slope = covariance / varianceX;
  const intercept = yMean - slope * xMean;
  const corr = covariance / Math.sqrt(varianceX * varianceY);

  return {
    slope: round(slope, 3),
    intercept: round(intercept, 3),
    corr: round(corr, 3),
  };
}

export function generateLidarForwardComposite3DData(turbineId: string): LidarForwardComposite3DResponse {
  const step = (forwardCompositeStepMap.get(turbineId) ?? 0) + 1;
  forwardCompositeStepMap.set(turbineId, step);
  const rand = createSeededRandom(`lidar-forward-composite-3d-${turbineId}-${step}`);
  const distances = [50, 70, 90, 110, 130, 150, 170, 180, 190, 200];
  const beamOffsets = [-0.18, -0.06, 0.05, 0.16];
  const turbineBias = (Number(getTurbineOrdinal(turbineId)) % 10) / 10;
  const hubBase = 8.6 + turbineBias * 0.08 + 0.28 * Math.sin(step / 8.5) + 0.12 * Math.sin(step / 3.7);
  const mainDir = 114 + turbineBias * 2 + 4 * Math.sin(step / 10.5) + 1.6 * Math.sin(step / 4.8);
  const rawPoints: LidarRawPoint3D[] = [];

  distances.forEach((distance) => {
    const ringRadius = 8 + distance * 0.035;
    const a = ringRadius / Math.sqrt(2);
    const corners: Array<[number, number]> = [
      [a, a],
      [-a, a],
      [-a, -a],
      [a, -a],
    ];
    const baseAtDistance =
      hubBase +
      0.42 * Math.sin(distance / 34 + step / 11) +
      0.15 * Math.sin(distance / 13 + step / 6.5);

    corners.forEach(([x, y], beamIndex) => {
      const dynamicBeamOffset = beamOffsets[beamIndex] + 0.05 * Math.sin(step / 7 + beamIndex * 0.9 + distance / 44);
      const windSpeed = clamp(baseAtDistance + dynamicBeamOffset + noise(rand, 0.06), 6.5, 11.5);
      const quality = round(clamp(0.84 + 0.05 * Math.sin(step / 9 + distance / 58 + beamIndex) + noise(rand, 0.06), 0.7, 1.0), 2);
      rawPoints.push({
        id: `raw-${distance}-${beamIndex}`,
        beamIndex: beamIndex as 0 | 1 | 2 | 3,
        distance,
        x: round(x, 2),
        y: round(y, 2),
        z: distance,
        windSpeed: round(windSpeed),
        isValid: true,
        quality,
      });
    });
  });

  const invalidSlots = [
    { distance: distances[(step + 1) % distances.length], beamIndex: ((step + 0) % 4) as 0 | 1 | 2 | 3 },
    { distance: distances[(step + 4) % distances.length], beamIndex: ((step + 2) % 4) as 0 | 1 | 2 | 3 },
    ...(step % 5 === 0
      ? [{ distance: distances[(step + 7) % distances.length], beamIndex: ((step + 1) % 4) as 0 | 1 | 2 | 3 }]
      : []),
  ];

  invalidSlots.forEach(({ distance, beamIndex }, index) => {
    const point = rawPoints.find((item) => item.distance === distance && item.beamIndex === beamIndex);
    if (!point) return;
    point.isValid = false;
    point.quality = round(clamp(0.32 + 0.06 * Math.sin(step / 4 + index) + noise(rand, 0.06), 0.2, 0.55), 2);
  });

  const synthPoints: LidarSynthPoint3D[] = distances.map((distance) => {
    const support = rawPoints.filter((item) => item.distance === distance && item.isValid);
    const validRawCount = support.length;
    const isValid = validRawCount >= 2;
    const meanWindSpeed = validRawCount
      ? support.reduce((sum, item) => sum + item.windSpeed, 0) / validRawCount
      : rawPoints.filter((item) => item.distance === distance).reduce((sum, item) => sum + item.windSpeed, 0) / 4;
    return {
      id: `synth-${distance}`,
      distance,
      x: 0,
      y: 0,
      z: distance,
      windSpeed: round(clamp(meanWindSpeed + noise(rand, 0.03), 6.5, 11.5)),
      windDirection: round(((mainDir + 3 * Math.sin(distance / 42 + step / 12) + noise(rand, 1.0)) % 360 + 360) % 360, 0),
      ti: round(clamp(8.5 + 1.1 * Math.sin(distance / 55 + step / 10) + noise(rand, 0.3), 6.5, 14.5), 1),
      isValid,
      validRawCount,
    };
  });

  return {
    turbineId,
    hubWindSpeed: round(synthPoints[0]?.windSpeed ?? hubBase),
    hubWindDirection: round(mainDir, 0),
    distances,
    rawPoints,
    synthPoints,
  };
}

export function generateLidarInflowProfilePanelData(turbineId: string): LidarInflowProfilePanelData {
  const now = Date.now() / 1000;
  const phase = (2 * Math.PI * now) / 48;
  const phaseSlow = (2 * Math.PI * now) / 120;
  const step = Math.floor(now / 3);
  const rand = createSeededRandom(`lidar-inflow-profile-${turbineId}-${step}`);
  const distances = [50, 75, 100, 125, 150, 175, 200, 225, 250, 275];
  const turbineBias = (Number(getTurbineOrdinal(turbineId)) % 10) / 10;
  const baseWind =
    8.1 +
    turbineBias * 0.12 +
    0.32 * Math.sin(phase + turbineBias) +
    0.14 * Math.sin(phaseSlow * 0.8 + turbineBias * 1.7) +
    rand() * 0.18;
  const activeDistance = distances[4];

  const profiles: LidarInflowProfilePoint[] = distances.map((distance, index) => {
    const ratio = index / (distances.length - 1);
    const windSpeed = clamp(
      baseWind +
        0.95 * (1 - Math.exp(-ratio * 2.4)) +
        0.18 * Math.sin(index / 2.1 + turbineBias + phase * 0.45) +
        0.06 * Math.sin(index / 0.95 + 0.3 + phaseSlow * 0.7) +
        noise(rand, 0.03),
      7.4,
      10.8,
    );
    const windDirection = ((116 +
      turbineBias * 3 +
      2.6 * Math.sin(index / 2.6 + 0.2 + phase * 0.32) +
      1.1 * Math.sin(index / 5.2 + 1.1 + phaseSlow * 0.55) +
      ratio * 1.8 +
      noise(rand, 0.25)) %
      360 +
      360) %
      360;
    const horizontalShear = clamp(
      0.048 +
        0.018 * Math.sin(index / 2.2 + 0.4 + phase * 0.4) +
        0.012 * (1 - Math.exp(-ratio * 2.1)) +
        0.004 * Math.sin(index / 0.9 + 0.7 + phaseSlow * 0.7) +
        noise(rand, 0.0025),
      0.01,
      0.14,
    );
    const verticalShear = clamp(
      0.058 +
        0.015 * Math.sin(index / 2.5 + 1.0 + phase * 0.36) +
        0.01 * ratio +
        0.004 * Math.sin(index / 1.05 + 2.1 + phaseSlow * 0.65) +
        noise(rand, 0.0025),
      0.015,
      0.15,
    );

    return {
      distance,
      windSpeed: round(windSpeed),
      windDirection: round(windDirection, 1),
      horizontalShear: round(horizontalShear, 3),
      verticalShear: round(verticalShear, 3),
    };
  });

  return { activeDistance, distances, profiles };
}

export function generateWindRoseTiStats(): WindRoseTiStats {
  const rand = createSeededRandom('wind-rose-ti-stats');
  const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
  const dominantIndex = 5;

  const sectors: WindRoseSector[] = directions.map((direction, index) => {
    const angularDistance = Math.min(Math.abs(index - dominantIndex), directions.length - Math.abs(index - dominantIndex));
    const dominance = Math.exp(-(angularDistance ** 2) / 5.4);
    const offsetToSecondary = (index - 11 + directions.length) % directions.length;
    const secondary = Math.exp(-((offsetToSecondary ** 2) / 26));
    const frequency = clamp(2.4 + dominance * 12.5 + secondary * 3.8 + noise(rand, 0.9), 1.2, 18.5);
    const ti = clamp(0.085 + dominance * 0.055 + Math.sin(index / 2.4) * 0.014 + noise(rand, 0.01), 0.06, 0.22);
    const meanWindSpeed = clamp(7.6 + dominance * 1.4 + Math.cos(index / 3.6) * 0.5 + noise(rand, 0.25), 6.4, 10.8);
    return {
      direction,
      angle: index * 22.5,
      frequency: round(frequency, 1),
      ti: round(ti, 3),
      meanWindSpeed: round(meanWindSpeed),
    };
  });

  return { sectors };
}

export function generateTransferFunctionData(): TransferFunctionData {
  const rand = createSeededRandom('transfer-function-data');
  const count = 48;
  const points: TransferFunctionPoint[] = [];

  for (let index = 0; index < count; index += 1) {
    const exponent = -2 + (2 * index) / (count - 1);
    const frequency = 10 ** exponent;
    const gain = clamp(
      1 / Math.sqrt(1 + (frequency / 0.19) ** 1.7) + Math.exp(-frequency * 5.5) * 0.04 + noise(rand, 0.018),
      0.08,
      1.04,
    );
    const phase = clamp(-Math.atan(frequency / 0.16) * (180 / Math.PI) * 1.08 + noise(rand, 1.8), -92, -2);
    points.push({
      frequency: round(frequency, 4),
      gain: round(gain, 3),
      phase: round(phase, 1),
    });
  }

  return {
    points,
    markerFrequencies: [0.1, 0.3],
  };
}

export function generateConsistencyAlignmentData(): ConsistencyAlignmentData {
  const rand = createSeededRandom('consistency-alignment-data');
  const points: ConsistencyAlignmentPoint[] = [];
  const count = 210;

  for (let index = 0; index < count; index += 1) {
    const lidarWindSpeed = clamp(5.8 + (index / count) * 6.4 + Math.sin(index / 11) * 0.5 + noise(rand, 0.48), 5.5, 12.6);
    const nacelleWindSpeed = clamp(lidarWindSpeed * 0.962 + 0.28 + noise(rand, 0.44), 5.2, 12.7);
    points.push({
      lidarWindSpeed: round(lidarWindSpeed),
      nacelleWindSpeed: round(nacelleWindSpeed),
    });
  }

  const regression = computeRegression(points);
  const bias = points.reduce((sum, item) => sum + (item.nacelleWindSpeed - item.lidarWindSpeed), 0) / points.length;
  const rmse = Math.sqrt(
    points.reduce((sum, item) => sum + (item.nacelleWindSpeed - item.lidarWindSpeed) ** 2, 0) / points.length,
  );

  return {
    points,
    regression: {
      slope: regression.slope,
      intercept: regression.intercept,
    },
    stats: {
      bias: round(bias, 3),
      rmse: round(rmse, 3),
      corr: regression.corr,
    },
  };
}

export function generateDataQualitySummary(): DataQualitySummary {
  return {
    qualityOverview: {
      topMetrics: [
        { key: 'availability', value: 96.97, unit: '%', status: 'excellent', progress: 0.9697, precision: 2 },
        { key: 'latency', value: 103, unit: 'ms', status: 'normal', progress: 0.78, precision: 0 },
        { key: 'packetLoss', value: 0.81, unit: '%', status: 'normal', progress: 0.92, precision: 2 },
        { key: 'timeSync', value: 4.6, unit: 'ms', prefix: '+', status: 'excellent', progress: 0.9, precision: 1 },
      ],
      bottomMetrics: [
        { key: 'snr', value: 14.6, unit: 'dB', status: 'good', progress: 0.73, precision: 1 },
        { key: 'validBeam', value: 95.0, unit: '%', status: 'excellent', progress: 0.95, precision: 1 },
        { key: 'freshness', value: 0.8, unit: 's', status: 'normal', progress: 0.84, precision: 1 },
        { key: 'qualityScore', value: 92, grade: 'A', status: 'excellent', progress: 0.92, highlight: true },
      ],
    },
  };
}
