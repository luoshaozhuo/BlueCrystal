import type {
  TurbineBaseInfo,
  TurbineRealtimeStatus,
} from '@/api/generated/openapi';

// 风机基础信息静态样本（用于 base-info 接口）
export const turbineBaseList: TurbineBaseInfo[] = [
  {
    id: '01',
    turbineType: '10MW',
    modelName: 'WT_10MW',
    lon: 112.374857,
    lat: 37.952314,
    height: 1177.55,
  },
  {
    id: '02',
    turbineType: '10MW',
    modelName: 'WT_10MW',
    lon: 112.359059,
    lat: 37.955164,
    height: 1263.44,
  },
  {
    id: '03',
    turbineType: '10MW',
    modelName: 'WT_10MW',
    lon: 112.35977,
    lat: 37.955802,
    height: 1260.54,
  },
  {
    id: '04',
    turbineType: '10MW',
    modelName: 'WT_10MW',
    lon: 112.35834,
    lat: 37.954179,
    height: 1252.53,
  },
  {
    id: '05',
    turbineType: '10MW',
    modelName: 'WT_10MW',
    lon: 112.358423,
    lat: 37.95244,
    height: 1236.5,
  },
  {
    id: '06',
    turbineType: '10MW',
    modelName: 'WT_10MW',
    lon: 112.359179,
    lat: 37.950649,
    height: 1251.48,
  },
  {
    id: '07',
    turbineType: '10MW',
    modelName: 'WT_10MW',
    lon: 112.361409,
    lat: 37.949417,
    height: 1246.54,
  },
  {
    id: '08',
    turbineType: '10MW',
    modelName: 'WT_10MW',
    lon: 112.363857,
    lat: 37.948869,
    height: 1252.32,
  },
  {
    id: '09',
    turbineType: '10MW',
    modelName: 'WT_10MW',
    lon: 112.368585,
    lat: 37.954036,
    height: 1112.61,
  },
  {
    id: '10',
    turbineType: '10MW',
    modelName: 'WT_10MW',
    lon: 112.367682,
    lat: 37.950551,
    height: 1211.35,
  },
];

// 各实时字段量程定义（用于初始化与增量约束）
const realtimeFieldRanges = {
  rotorSpeed: [5, 20],
  rotorAzimuth: [0, 360],
  pitch1: [0, 30],
  pitch2: [0, 30],
  pitch3: [0, 30],
  yawAngle: [0, 360],
  activePower: [0, 10],
  reactivePower: [0, 1],
  windSpeed: [4, 12],
  windDirection: [-10, 10],
} as const;

const defaultVarianceRatio = 0.1;

// 读取噪声强度配置：VITE_MOCK_RT_VARIANCE_RATIO，非法时回退默认值
function getVarianceRatio() {
  const rawValue = import.meta.env.VITE_MOCK_RT_VARIANCE_RATIO;
  const parsed = Number.parseFloat(rawValue ?? '');

  if (!Number.isFinite(parsed) || parsed <= 0) {
    return defaultVarianceRatio;
  }

  return parsed;
}

const varianceRatio = getVarianceRatio();
const fallbackDeltaSeconds = 1;
const maximumDeltaSeconds = 5;
const fullCircleDegrees = 360;

type RealtimeNumericField = keyof typeof realtimeFieldRanges;
type RealtimeState = Omit<TurbineRealtimeStatus, 'id' | 'timestamp'>;

// 按风机 ID 缓存上一时刻状态，实现“增量变化”
const turbineRealtimeState = new Map<string, RealtimeState>();
const turbineLastTimestampSeconds = new Map<string, number>();

// 数值裁剪到闭区间
function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

// 按指定位数四舍五入
function round(value: number, digits: number) {
  const scale = 10 ** digits;
  return Math.round(value * scale) / scale;
}

function normalizeAngleDegrees(value: number) {
  if (!Number.isFinite(value)) return 0;
  let normalized = value % fullCircleDegrees;
  if (normalized < 0) normalized += fullCircleDegrees;
  if (normalized >= fullCircleDegrees) return 0;
  return normalized;
}

function roundAngleDegrees(value: number, digits = 2) {
  return normalizeAngleDegrees(round(normalizeAngleDegrees(value), digits));
}

// 均匀分布采样（初始状态使用）
function randomUniform(min: number, max: number) {
  return min + (max - min) * Math.random();
}

// 标准正态分布采样（Box-Muller）
function randomNormal() {
  let u = 0;
  let v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

// 环绕型字段归一化到区间（适用于角度）
function wrapInRange(value: number, min: number, max: number) {
  const span = max - min;
  if (span <= 0) return min;
  let wrapped = (value - min) % span;
  if (wrapped < 0) wrapped += span;
  return wrapped + min;
}

// 初始化实时状态：每个字段在量程内均匀采样
function createInitialRealtimeState(): RealtimeState {
  return {
    rotorSpeed: round(randomUniform(...realtimeFieldRanges.rotorSpeed), 2),
    rotorAzimuth: roundAngleDegrees(
      randomUniform(...realtimeFieldRanges.rotorAzimuth),
      2,
    ),
    pitch1: round(randomUniform(...realtimeFieldRanges.pitch1), 2),
    pitch2: round(randomUniform(...realtimeFieldRanges.pitch2), 2),
    pitch3: round(randomUniform(...realtimeFieldRanges.pitch3), 2),
    yawAngle: roundAngleDegrees(
      randomUniform(...realtimeFieldRanges.yawAngle),
      2,
    ),
    activePower: round(randomUniform(...realtimeFieldRanges.activePower), 3),
    reactivePower: round(
      randomUniform(...realtimeFieldRanges.reactivePower),
      3,
    ),
    windSpeed: round(randomUniform(...realtimeFieldRanges.windSpeed), 2),
    windDirection: round(
      randomUniform(...realtimeFieldRanges.windDirection),
      2,
    ),
  };
}

// 单字段增量更新：
// 均值 = 0，方差 = varianceRatio * 字段量程，随后按字段规则做环绕或截断
function nextFieldValue(field: RealtimeNumericField, prev: number) {
  const [min, max] = realtimeFieldRanges[field];
  const range = max - min;
  const variance = varianceRatio * range;
  const stdDev = Math.sqrt(variance);
  const delta = randomNormal() * stdDev;
  const rawValue = prev + delta;

  if (field === 'rotorAzimuth' || field === 'yawAngle') {
    return normalizeAngleDegrees(wrapInRange(rawValue, min, max));
  }

  return clamp(rawValue, min, max);
}

function resolveDeltaSeconds(
  currentTimeSeconds: number,
  previousTimestampSeconds?: number,
) {
  if (!Number.isFinite(previousTimestampSeconds ?? NaN)) {
    return fallbackDeltaSeconds;
  }
  const rawDelta = currentTimeSeconds - (previousTimestampSeconds as number);
  if (!Number.isFinite(rawDelta) || rawDelta <= 0) {
    return fallbackDeltaSeconds;
  }
  return Math.min(rawDelta, maximumDeltaSeconds);
}

function nextRotorAzimuth(
  previousAzimuth: number,
  rotorSpeedRpm: number,
  deltaSeconds: number,
) {
  const [minAzimuth, maxAzimuth] = realtimeFieldRanges.rotorAzimuth;
  const nextAzimuth = previousAzimuth + rotorSpeedRpm * 6 * deltaSeconds;
  return normalizeAngleDegrees(
    wrapInRange(nextAzimuth, minAzimuth, maxAzimuth),
  );
}

// 基于上一时刻状态生成下一时刻状态
function createNextRealtimeState(
  previousState: RealtimeState,
  deltaSeconds: number,
): RealtimeState {
  const rotorSpeed = round(
    nextFieldValue('rotorSpeed', previousState.rotorSpeed),
    2,
  );
  return {
    rotorSpeed,
    rotorAzimuth: roundAngleDegrees(
      nextRotorAzimuth(previousState.rotorAzimuth, rotorSpeed, deltaSeconds),
      2,
    ),
    pitch1: round(nextFieldValue('pitch1', previousState.pitch1), 2),
    pitch2: round(nextFieldValue('pitch2', previousState.pitch2), 2),
    pitch3: round(nextFieldValue('pitch3', previousState.pitch3), 2),
    yawAngle: roundAngleDegrees(
      nextFieldValue('yawAngle', previousState.yawAngle),
      2,
    ),
    activePower: round(
      nextFieldValue('activePower', previousState.activePower),
      3,
    ),
    reactivePower: round(
      nextFieldValue('reactivePower', previousState.reactivePower),
      3,
    ),
    windSpeed: round(nextFieldValue('windSpeed', previousState.windSpeed), 2),
    windDirection: round(
      nextFieldValue('windDirection', previousState.windDirection),
      2,
    ),
  };
}

// 生成单台风机实时状态，并回写缓存状态
function createRealtimeByTurbine(
  turbine: TurbineBaseInfo,
  currentTimeSeconds: number,
): TurbineRealtimeStatus {
  const previousState =
    turbineRealtimeState.get(turbine.id) ?? createInitialRealtimeState();
  const previousTimestampSeconds = turbineLastTimestampSeconds.get(turbine.id);
  const deltaSeconds = resolveDeltaSeconds(
    currentTimeSeconds,
    previousTimestampSeconds,
  );
  const nextState = createNextRealtimeState(previousState, deltaSeconds);
  turbineRealtimeState.set(turbine.id, nextState);
  turbineLastTimestampSeconds.set(turbine.id, currentTimeSeconds);

  return {
    id: turbine.id,
    timestamp: new Date(currentTimeSeconds * 1000).toISOString(),
    ...nextState,
  };
}

// base-info 数据构造
export function createTurbineBaseInfoData(): TurbineBaseInfo[] {
  return turbineBaseList.map((turbine) => ({ ...turbine }));
}

// realtime-status 数据构造（可按 ids 过滤）
export function createTurbineRealtimeStatusData(
  currentTimeMs = Date.now(),
  ids?: string[],
): TurbineRealtimeStatus[] {
  const currentTimeSeconds = currentTimeMs / 1000;
  const idFilter =
    ids && ids.length > 0
      ? new Set(ids.map((id) => id.trim()).filter(Boolean))
      : null;
  const sourceList = idFilter
    ? turbineBaseList.filter((turbine) => idFilter.has(turbine.id))
    : turbineBaseList;

  return sourceList.map((turbine) =>
    createRealtimeByTurbine(turbine, currentTimeSeconds),
  );
}
