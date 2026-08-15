/**
 * 汇总激光雷达页面使用的本地数据生成函数。
 * 生产代码通过这里读取演示数据，避免直接依赖 mock 注册入口。
 */
export {
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
  resetTopRealtimeWindWave,
} from '@/mock/lidar/rules';
