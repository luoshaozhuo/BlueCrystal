import Mock from 'mockjs';
import setupMock, { successResponseWrap } from '@/utils/setup-mock';
import {
  createGustResponseCardMock,
  volatilityEvidence,
  powerCurveSeries,
  summaryMetrics,
  turbineOptions,
  turbineProfiles,
  windFrequencyRayleighParameters,
} from '@/api/local-data/power-analysis';

setupMock({
  setup() {
    Mock.mock(new RegExp('/api/power-analysis/page'), () => {
      return successResponseWrap({
        turbineOptions,
        turbineProfiles,
        summaryMetrics,
        powerCurveSeries,
        windFrequencyRayleighParameters,
        gustResponseCardData: createGustResponseCardMock(),
        volatilityEvidence,
      });
    });
  },
});

export * from './rules';
export {
  turbineOptions,
  turbineProfiles,
  windFrequencyRayleighParameters,
} from './fixtures';
