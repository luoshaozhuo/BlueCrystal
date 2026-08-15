export interface LidarTurbineOption {
  label: string;
  value: string;
}

export interface LidarDeviceInfo {
  deviceModel: string;
  deviceId: string;
  scanMode: '1D' | '2D' | '3D';
  scanLayers: number;
  scanAngleRange: string;
  sampleFrequencyHz: number;
}

export interface LidarTopMetricItem {
  key: string;
  value: number | string;
  unit?: string;
  status?: 'normal' | 'warning' | 'offline';
  trend?: number;
  precision?: number;
}

export interface RealtimeWindWavePoint {
  ts: string;
  windSpeed: number;
}

export interface RealtimeWindWaveResponse {
  points: RealtimeWindWavePoint[];
  current: number;
  mean60s: number;
  min60s: number;
  max60s: number;
}

export interface LidarRawPoint3D {
  id: string;
  beamIndex: 0 | 1 | 2 | 3;
  distance: number;
  x: number;
  y: number;
  z: number;
  windSpeed: number;
  isValid: boolean;
  quality: number;
}

export interface LidarSynthPoint3D {
  id: string;
  distance: number;
  x: number;
  y: number;
  z: number;
  windSpeed: number;
  windDirection: number;
  ti: number;
  isValid: boolean;
  validRawCount: number;
}

export interface LidarForwardComposite3DResponse {
  turbineId: string;
  hubWindSpeed: number;
  hubWindDirection: number;
  distances: number[];
  rawPoints: LidarRawPoint3D[];
  synthPoints: LidarSynthPoint3D[];
}

export interface LidarInflowProfilePoint {
  distance: number;
  windSpeed: number;
  windDirection: number;
  horizontalShear: number;
  verticalShear: number;
}

export interface LidarInflowProfilePanelData {
  activeDistance: number;
  distances: number[];
  profiles: LidarInflowProfilePoint[];
}

export interface WindRoseSector {
  direction: string;
  angle: number;
  frequency: number;
  ti: number;
  meanWindSpeed: number;
}

export interface WindRoseTiStats {
  sectors: WindRoseSector[];
}

export interface TransferFunctionPoint {
  frequency: number;
  gain: number;
  phase: number;
}

export interface TransferFunctionData {
  points: TransferFunctionPoint[];
  markerFrequencies: number[];
}

export interface ConsistencyAlignmentPoint {
  lidarWindSpeed: number;
  nacelleWindSpeed: number;
}

export interface ConsistencyAlignmentStats {
  bias: number;
  rmse: number;
  corr: number;
}

export interface ConsistencyRegression {
  slope: number;
  intercept: number;
}

export interface ConsistencyAlignmentData {
  points: ConsistencyAlignmentPoint[];
  regression: ConsistencyRegression;
  stats: ConsistencyAlignmentStats;
}

export interface DataQualityMetricItem {
  key: string;
  value: number | string;
  grade?: string;
  unit?: string;
  prefix?: string;
  status: 'excellent' | 'good' | 'normal' | 'warning';
  progress: number;
  highlight?: boolean;
  precision?: number;
}

export interface DataQualityOverview {
  topMetrics: DataQualityMetricItem[];
  bottomMetrics: DataQualityMetricItem[];
}

export interface DataQualitySummary {
  qualityOverview: DataQualityOverview;
}
