/**
 * 汇总载荷缓解页面的本地演示数据与类型。
 * 该出口只暴露纯计算逻辑，供页面和开发态 mock 共同复用。
 */
export {
  createLoadMitigationMetricConfigMap,
  createLoadMitigationPageMock,
} from '@/mock/load-mitigation/rules';

export {
  loadMitigationHighAmplitudeBins,
  loadMitigationKpiList,
  loadMitigationTurbineMeta,
  loadMitigationTurbineOptions,
} from '@/mock/load-mitigation/fixtures';

export type { LoadMetricKey } from '@/mock/load-mitigation/fixtures';
export type { LoadMitigationMetricConfig } from '@/mock/load-mitigation/rules';
