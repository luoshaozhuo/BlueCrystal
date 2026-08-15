import Mock from 'mockjs';
import setupMock, { successResponseWrap } from '@/utils/setup-mock';
import {
  generateConsistencyAlignmentData,
  generateDataQualitySummary,
  generateLidarDeviceInfo,
  generateLidarForwardComposite3DData,
  generateLidarInflowProfilePanelData,
  generateLidarTopMetrics,
  generateLidarTurbineOptions,
  generateTopRealtimeWindWave,
  generateTransferFunctionData,
  generateWindRoseTiStats,
} from '@/api/local-data/lidar';

setupMock({
  setup() {
    Mock.mock(new RegExp('/api/lidar/page'), () => {
      return successResponseWrap({
        turbineOptions: generateLidarTurbineOptions(),
        deviceInfo: generateLidarDeviceInfo('WT-07'),
        topMetrics: generateLidarTopMetrics('WT-07'),
        realtimeWindWave: generateTopRealtimeWindWave('WT-07'),
        forwardComposite3d: generateLidarForwardComposite3DData('WT-07'),
        inflowProfile: generateLidarInflowProfilePanelData('WT-07'),
        windRoseTiStats: generateWindRoseTiStats(),
        transferFunction: generateTransferFunctionData(),
        consistencyAlignment: generateConsistencyAlignmentData(),
        dataQualitySummary: generateDataQualitySummary(),
      });
    });
  },
});

export * from './fixtures';
export * from './rules';
