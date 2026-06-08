/**
 * 提供采集概览页在生产环境可直接消费的本地演示数据。
 * 该模块只暴露纯数据生成逻辑，不注册 Mock XHR 拦截。
 */
export {
  getDataAcquisitionTopMetrics,
  getDataCollectionMock,
} from '@/mock/data-acquisition/rules';

export type {
  ChannelCompositionKey,
  ChannelHealthMetricKey,
  ChannelResourceData,
  ComputeResourceData,
  ComputeServiceKey,
  DataAcquisitionTopMetricKey,
  DataCollectionMock,
  DataQualityAnalysisData,
  DataQualityAnomalyKey,
  DataQualityLatencyKey,
  DataQualitySyncBinKey,
  DeviceCommItem,
  DeviceCommStatus,
  StoragePartitionKey,
  StorageResourceData,
} from '@/mock/data-acquisition/rules';
