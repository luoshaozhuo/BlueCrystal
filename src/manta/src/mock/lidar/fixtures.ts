import type { LidarDeviceInfo, LidarTurbineOption } from '@/types/lidar';

export const lidarTurbineOptionsFixture: LidarTurbineOption[] = [
  { label: 'WT-07', value: 'WT-07' },
  { label: 'WT-12', value: 'WT-12' },
  { label: 'WT-18', value: 'WT-18' },
  { label: 'WT-23', value: 'WT-23' },
];

export const lidarModeMapFixture: Record<string, LidarDeviceInfo['scanMode']> = {
  'WT-07': '3D',
  'WT-12': '2D',
  'WT-18': '3D',
  'WT-23': '1D',
};
