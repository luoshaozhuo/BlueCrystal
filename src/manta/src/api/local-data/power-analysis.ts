/**
 * 汇总功率分析页使用的本地演示数据。
 * 该模块隔离了 mock 注册边界，避免生产包引入 mockjs。
 */
export {
  createGustResponseCardMock,
  gustResponseCardData,
  powerCurveSeries,
  summaryMetrics,
  turbineOptions,
  turbineProfiles,
  volatilityEvidence,
  windFrequencyRayleighParameters,
} from '@/mock/power-analysis/rules';
